import XCTest
import CoreLocation
import CameraCore
@testable import FineMeNot

/// Contract simulation at the OS boundary. Uses the shipping controller,
/// retry loop, fix filtering, alert engine and encounter persistence.
@MainActor
final class MonitoringWakeTests: XCTestCase {
    final class Source: MonitoringLocationService {
        var authorization: CLAuthorizationStatus = .authorizedAlways
        var precise = true
        var isForeground = false
        var authorizationChanged: (() -> Void)?
        var recoveredLocation: ((CLLocation) -> Void)?
        var recoveryFailed: ((CLError.Code?) -> Void)?
        var starts = 0, stops = 0, cancellations = 0
        var navigationRequests: [Bool] = []
        var streams: [AsyncThrowingStream<MonitoringLocationUpdate, Error>.Continuation] = []
        func requestLegacyAuthorization() {}
        func beginSession() { starts += 1 }
        func endSession() { stops += 1 }
        func updates(_ configuration: CLLocationUpdate.LiveConfiguration) -> AsyncThrowingStream<MonitoringLocationUpdate, Error> {
            if case .automotiveNavigation = configuration { navigationRequests.append(true) }
            else { navigationRequests.append(false) }
            let (stream, continuation) = AsyncThrowingStream<MonitoringLocationUpdate, Error>.makeStream()
            continuation.onTermination = { [weak self] _ in
                Task { @MainActor in self?.cancellations += 1 }
            }
            streams.append(continuation)
            return stream
        }
        func send(_ event: MonitoringLocationUpdate) { streams.last!.yield(event) }
    }
    final class Store: MonitoringCameraStore {
        let snapshot: CameraSnapshot?
        let index: CameraIndex
        var isDue = false
        init() throws {
            let camera = Camera(id: "wake-camera", label: "Fixture road", kind: .speed,
                                geometry: [Coordinate(35.0054, -106)], travelBearing: 0,
                                sourceIDs: ["fixture"], evidence: "Synthetic camera")
            index = CameraIndex(cameras: [camera])
            let data = try JSONSerialization.data(withJSONObject: [
                "schemaVersion": 1, "version": "fixture", "generatedAt": "2026-09-27T00:00:00Z",
                "coverage": "Test only", "sources": [],
                "cameras": [try JSONSerialization.jsonObject(with: JSONEncoder().encode(camera))]
            ])
            snapshot = try CameraSnapshot.decode(data)
        }
        func refresh(force: Bool) async -> Bool { XCTFail("Unexpected database work during wake test"); return false }
    }
    final class Presenter: MonitoringWarningPresenter {
        var warnings: [CameraWarning] = []
        func present(_ warnings: [CameraWarning]) { self.warnings += warnings }
        func requestNotifications() async {}
    }
    @MainActor final class Clock {
        var date = Date(timeIntervalSince1970: 1_790_500_000)
        func advance(_ seconds: TimeInterval) { date += seconds }
    }
    actor RetryGate {
        var waits = 0
        private var continuation: CheckedContinuation<Void, Never>?
        func wait() async {
            waits += 1
            await withCheckedContinuation { continuation = $0 }
        }
        func release() { continuation?.resume(); continuation = nil }
    }
    @MainActor struct Rig {
        let controller: MonitoringController
        let source: Source
        let presenter: Presenter
        let clock: Clock
        let gate: RetryGate
        let defaults: UserDefaults
        let suite: String
        init() throws {
            let source = Source(), presenter = Presenter(), clock = Clock(), gate = RetryGate()
            let suite = "wake-tests-\(UUID().uuidString)"
            let defaults = UserDefaults(suiteName: suite)!
            defaults.set(true, forKey: "warnings.enabled")
            self.source = source; self.presenter = presenter; self.clock = clock; self.gate = gate
            self.defaults = defaults; self.suite = suite
            controller = MonitoringController(store: try Store(), presenter: presenter, defaults: defaults,
                                              locationService: source, now: { clock.date },
                                              waitToRetry: { await gate.wait() })
            controller.start()
        }
        func close() async {
            controller.setEnabled(false)
            await gate.release()
            defaults.removePersistentDomain(forName: suite)
        }
        func fix(accuracy: Double = 5, speed: Double = 25, age: Double = 0, latitude: Double = 35.0033) -> CLLocation {
            CLLocation(coordinate: CLLocationCoordinate2D(latitude: latitude, longitude: -106),
                       altitude: 0, horizontalAccuracy: accuracy, verticalAccuracy: 5,
                       course: 0, courseAccuracy: 1, speed: speed, speedAccuracy: 0.5,
                       timestamp: clock.date.addingTimeInterval(-age))
        }
        func pause() { source.send(.init(stationary: true, location: fix(speed: 0, latitude: 35))) }
    }
    func eventually(_ description: String = "event delivered", file: StaticString = #filePath, line: UInt = #line, _ check: @escaping @MainActor () -> Bool) async {
        let deadline = ContinuousClock.now + .seconds(3)
        while !check(), ContinuousClock.now < deadline { try? await Task.sleep(for: .milliseconds(5)) }
        XCTAssertTrue(check(), description, file: file, line: line)
    }

    func testOvernightPauseKeepsNavigationArmedThenWarnsOnce() async throws {
        let r = try Rig()
        r.pause(); await eventually { r.controller.stationary }
        r.clock.advance(8 * 3600)
        r.controller.start() // Repeated lifecycle/recovery start while idle.
        XCTAssertEqual(r.controller.status(at: r.clock.date), "Ready · waiting for movement")
        XCTAssertEqual(r.source.starts, 1); XCTAssertEqual(r.source.stops, 0)
        XCTAssertEqual(r.source.cancellations, 0); XCTAssertEqual(r.source.navigationRequests, [true])
        XCTAssertTrue(r.presenter.warnings.isEmpty)
        r.source.send(.init(stationary: false)) // Resume without a fix or speed.
        await eventually { !r.controller.stationary }
        XCTAssertEqual(r.controller.status(at: r.clock.date), "Waiting for location")
        r.source.send(.init(stationary: false, location: r.fix(accuracy: 300)))
        await eventually { r.controller.lastAccuracy == 300 }
        XCTAssertTrue(r.presenter.warnings.isEmpty)
        XCTAssertTrue(r.controller.isTracking)
        r.clock.advance(3)
        r.source.send(.init(stationary: false, location: r.fix()))
        await eventually { r.presenter.warnings.count == 1 }
        XCTAssertTrue(r.controller.locationResumeDiagnostic.contains("300.0 m"))
        XCTAssertTrue(r.controller.locationResumeDiagnostic.contains("3.0 seconds"))
        r.clock.advance(2); r.source.send(.init(stationary: false, location: r.fix()))
        await eventually { r.controller.lastFixAt == r.clock.date }
        XCTAssertEqual(r.presenter.warnings.count, 1)
        XCTAssertEqual(r.source.navigationRequests, [true])
        await r.close(); await eventually { r.source.cancellations == 1 }
        XCTAssertEqual(r.source.stops, 1)
    }

    func testStaleAndMissingFixesCannotWarnOrPreventLaterRecovery() async throws {
        let r = try Rig(); r.pause(); await eventually { r.controller.stationary }
        r.clock.advance(3600)
        r.source.send(.init(stationary: false, problem: .unavailable))
        await eventually { r.controller.failure != nil }
        XCTAssertFalse(r.controller.stationary)
        r.source.send(.init(stationary: false, location: r.fix(age: 60)))
        await eventually { r.controller.fixStatus.hasPrefix("Rejected") }
        XCTAssertEqual(r.controller.warningCount, 0)
        r.clock.advance(1); r.source.send(.init(stationary: false, location: r.fix()))
        await eventually { r.controller.warningCount == 1 }
        XCTAssertNil(r.controller.failure)
        await r.close()
    }

    func testSlowDepartureClearsPauseBeforeWarningSpeedThreshold() async throws {
        let r = try Rig(); r.pause(); await eventually { r.controller.stationary }
        r.clock.advance(300)
        r.source.send(.init(stationary: false, location: r.fix(speed: 0.5)))
        await eventually { !r.controller.stationary }
        XCTAssertEqual(r.controller.lastFixAt, r.clock.date)
        XCTAssertTrue(r.presenter.warnings.isEmpty)
        XCTAssertEqual(r.source.navigationRequests, [true])
        r.clock.advance(1); r.source.send(.init(stationary: false, location: r.fix()))
        await eventually { r.controller.warningCount == 1 }
        await r.close()
    }

    func testStopDuringPauseRejectsOldEventsAfterRestart() async throws {
        let r = try Rig(); r.pause(); await eventually { r.controller.stationary }
        let old = r.source.streams[0]
        r.controller.setEnabled(false)
        XCTAssertFalse(r.controller.isTracking)
        r.controller.setEnabled(true)
        old.yield(.init(stationary: true, problem: .authorization)); old.finish()
        r.clock.advance(1)
        r.source.send(.init(stationary: false, location: r.fix()))
        await eventually { r.controller.warningCount == 1 }
        XCTAssertTrue(r.controller.isTracking); XCTAssertFalse(r.controller.stationary)
        XCTAssertNil(r.controller.failure); XCTAssertEqual(r.source.navigationRequests, [true, true])
        await r.close()
    }

    func testEndedAndFailedStreamsRetryNavigationAndCanResume() async throws {
        enum Failure: Error { case fixture }
        for fail in [false, true] {
            let r = try Rig(); r.pause(); await eventually { r.controller.stationary }
            r.source.streams[0].finish(throwing: fail ? Failure.fixture : nil)
            await eventually { !r.controller.isTracking }
            // Wait for the actual retry task to suspend at the controlled clock.
            for _ in 0..<100 where await r.gate.waits == 0 { try await Task.sleep(for: .milliseconds(5)) }
            let waits = await r.gate.waits; XCTAssertEqual(waits, 1)
            XCTAssertEqual(r.source.stops, 0) // Background eligibility spans retry.
            await r.gate.release()
            await eventually { r.source.streams.count == 2 }
            r.clock.advance(1)
            r.source.send(.init(stationary: false, location: r.fix()))
            await eventually { r.controller.warningCount == 1 }
            XCTAssertEqual(r.source.navigationRequests, [true, true])
            await r.close()
        }
    }

    func testCancelledRetryCannotStartAThirdProvider() async throws {
        let r = try Rig(); r.source.streams[0].finish()
        await eventually { !r.controller.isTracking }
        for _ in 0..<100 where await r.gate.waits == 0 { try await Task.sleep(for: .milliseconds(5)) }
        r.controller.setEnabled(false); r.controller.setEnabled(true)
        await r.gate.release()
        r.source.send(.init(stationary: false, location: r.fix()))
        await eventually { r.controller.warningCount == 1 }
        XCTAssertEqual(r.source.streams.count, 2)
        await r.close()
    }

    func testPermissionLossStopsAndRestorationRestartsWithoutForeground() async throws {
        let r = try Rig(); r.pause(); await eventually { r.controller.stationary }
        r.source.authorization = .denied; r.source.authorizationChanged?()
        XCTAssertFalse(r.controller.isTracking); XCTAssertEqual(r.source.stops, 1)
        XCTAssertEqual(r.controller.status(at: r.clock.date), "Location access needed")
        r.source.authorization = .authorizedAlways; r.source.authorizationChanged?()
        r.clock.advance(1)
        r.source.send(.init(stationary: false, location: r.fix()))
        await eventually { r.controller.warningCount == 1 }
        XCTAssertFalse(r.source.isForeground)
        XCTAssertEqual(r.source.navigationRequests, [true, true])
        await r.close()
    }

    func testRecoveryManagerErrorsDoNotTearDownHealthyPausedStream() async throws {
        let r = try Rig(); r.pause(); await eventually { r.controller.stationary }
        for error: CLError.Code in [.locationUnknown, .network, .denied] { r.source.recoveryFailed?(error) }
        XCTAssertTrue(r.controller.isTracking); XCTAssertTrue(r.controller.stationary)
        XCTAssertNil(r.controller.failure); XCTAssertEqual(r.source.stops, 0)
        r.clock.advance(300); r.source.send(.init(stationary: false, location: r.fix()))
        await eventually { r.controller.warningCount == 1 }
        await r.close()
    }

    func testSavedEnabledStateRecreatesMonitoringButDoesNotRepeatEncounter() async throws {
        let r = try Rig(); r.source.send(.init(stationary: false, location: r.fix()))
        await eventually { r.controller.warningCount == 1 }
        r.controller.setEnabled(false)
        r.defaults.set(true, forKey: "warnings.enabled") // Preference survives a permitted system relaunch.
        let source = Source(), presenter = Presenter()
        let relaunched = MonitoringController(store: try Store(), presenter: presenter, defaults: r.defaults,
                                              locationService: source, now: { r.clock.date })
        relaunched.start(); r.clock.advance(2)
        source.send(.init(stationary: false, location: r.fix()))
        await eventually { relaunched.lastFixAt == r.clock.date }
        XCTAssertEqual(source.navigationRequests, [true]); XCTAssertTrue(presenter.warnings.isEmpty)
        XCTAssertEqual(relaunched.matchDiagnostic.reason, .cooldown)
        relaunched.setEnabled(false); await r.close()
    }

    func testCandidateChannelDoesNotReadNewerPublicCameraCache() throws {
        let root = FileManager.default.temporaryDirectory.appending(path: UUID().uuidString)
        let publicCache = root.appending(path: "FineMeNot")
        try FileManager.default.createDirectory(at: publicCache, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: root) }
        let bundledURL = try XCTUnwrap(Bundle.main.url(forResource: "cameras", withExtension: "json"))
        let data = try Data(contentsOf: bundledURL)
        let bundled = try CameraSnapshot.decode(data)
        var newer = try XCTUnwrap(JSONSerialization.jsonObject(with: data) as? [String: Any])
        newer["version"] = "newer-public-snapshot"
        newer["generatedAt"] = ISO8601DateFormatter().string(from: Date.now.addingTimeInterval(60))
        try JSONSerialization.data(withJSONObject: newer).write(to: publicCache.appending(path: "cameras.json"))

        let publicStore = CameraStore(baseURL: AppLinks.publicDatabase, supportDirectory: root)
        XCTAssertEqual(publicStore.snapshot?.version, "newer-public-snapshot")
        let candidate = CameraStore(baseURL: URL(string: "https://example.invalid/candidate/")!, supportDirectory: root)
        XCTAssertEqual(candidate.snapshot?.version, bundled.version)
        XCTAssertEqual(candidate.snapshot?.cameras, bundled.cameras)
    }
}
