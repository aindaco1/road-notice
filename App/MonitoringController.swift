import Foundation
import Observation
import CoreLocation
import UIKit
import CameraCore
#if DEBUG
import OSLog
#endif

@MainActor @Observable
final class MonitoringController {
    private(set) var enabled: Bool
    private(set) var quietBelowSpeedLimit: Bool
    private(set) var authorization = CLAuthorizationStatus.notDetermined
    private(set) var precise = true
    private(set) var lastFixAt: Date?
    private(set) var lastReceivedAt: Date?
    private(set) var lastAccuracy: Double?
    private(set) var lastReportedSpeed: Double?
    private(set) var lastSpeedAccuracy: Double?
    private(set) var fixStatus = "No location received"
    var stationary: Bool { streamState.stationary }
    private(set) var failure: String?
    private(set) var warningCount = 0
    var isTracking: Bool { streamState.isTracking }
    var locationPowerStatus: String {
        guard isTracking else { return "off" }
        return stationary ? "stationary · automatic resume armed" : "automotive navigation"
    }
    var locationResumeDiagnostic: String {
        guard isTracking else { return "Location monitoring is off" }
        guard streamState.resumedAt != nil else { return "No automatic resume observed this session" }
        let accuracy = streamState.firstResumedAccuracy.map { String(format: "%.1f m", $0) } ?? "unavailable"
        let delay = streamState.resumedUsableFixDelay.map { String(format: "%.1f seconds", $0) } ?? "waiting"
        return "First resumed accuracy: \(accuracy) · usable fix after resume event: \(delay)"
    }
    private let locationService: any MonitoringLocationService
    private let now: () -> Date
    private let waitToRetry: @Sendable () async throws -> Void
    private let defaults: UserDefaults
    private let store: any MonitoringCameraStore
    private let presenter: any MonitoringWarningPresenter
    private var updates: Task<Void, Never>?
    private var streamState = LocationStreamState()
    private var retry: Task<Void, Never>?
    private var engine: AlertEngine
    var matchDiagnostic: MatchDiagnostic { engine.diagnostic }

    init(store: any MonitoringCameraStore, presenter: any MonitoringWarningPresenter,
         defaults: UserDefaults = .standard, locationService: any MonitoringLocationService = CoreLocationService(),
         now: @escaping () -> Date = { .now },
         waitToRetry: @escaping @Sendable () async throws -> Void = { try await Task.sleep(for: .seconds(10)) }) {
        self.locationService = locationService; self.now = now; self.waitToRetry = waitToRetry
        self.store = store; self.presenter = presenter; self.defaults = defaults
        enabled = defaults.bool(forKey: "warnings.enabled")
        quietBelowSpeedLimit = SpeedCheck.isEnabled(in: defaults)
        let saved = defaults.data(forKey: "warnings.encounters")
            .flatMap { try? JSONDecoder().decode([String: Encounter].self, from: $0) } ?? [:]
        engine = AlertEngine(encounters: saved)
        locationService.authorizationChanged = { [weak self] in
            guard let self else { return }
            self.refreshAuthorization()
            if self.authorization == .denied || self.authorization == .restricted { self.stop() }
            else { self.start() }
        }
        locationService.recoveredLocation = { [weak self] location in
            guard let self, self.enabled else { return }
            self.start(); self.consume(location)
        }
        locationService.recoveryFailed = { [weak self] code in self?.recoveryFailed(code) }
        refreshAuthorization()
    }

    func setEnabled(_ value: Bool) {
        enabled = value; defaults.set(value, forKey: "warnings.enabled")
        if value {
            start()
            Task { await presenter.requestNotifications() }
        } else { stop() }
    }

    func setQuietBelowSpeedLimit(_ value: Bool) {
        quietBelowSpeedLimit = value
        defaults.set(value, forKey: SpeedCheck.preferenceKey)
    }

    func start() {
        guard enabled else { return }
        locationService.requestLegacyAuthorization()
        guard !isTracking else { return }
        retry?.cancel(); retry = nil; failure = nil
        refreshAuthorization()
        guard authorization != .denied && authorization != .restricted else { return }
        guard authorization != .notDetermined || locationService.isForeground else { return }
        // Keep the automotive stream and sessions alive through stationary
        // pauses. Core Location then resumes it on movement, including after
        // suspension; no foreground timer or minimum warning speed is involved.
        locationService.beginSession()
        guard let sessionID = streamState.begin() else { return }
        SupportDiagnostics.shared.record("monitoring", ["monitoring": "requested"])
        let source = locationService.updates(.automotiveNavigation)
        updates = Task { [weak self] in
            do {
                for try await update in source {
                    guard !Task.isCancelled, let self, self.enabled,
                          self.streamState.isCurrent(sessionID) else { break }
                    self.receive(update, sessionID: sessionID)
                }
            } catch {
                // The common completion path retries both errors and an
                // unexpectedly finished sequence without creating a second one.
            }
            guard !Task.isCancelled, let self, self.streamState.end(sessionID) else { return }
            self.updates = nil
            self.failure = "Location failed. Retrying automatically."
            if self.enabled { self.scheduleRetry() }
        }
    }

    private func scheduleRetry() {
        guard retry == nil else { return }
        let wait = waitToRetry
        retry = Task { [weak self] in
            do { try await wait() } catch { return }
            guard !Task.isCancelled, let self else { return }
            self.retry = nil
            self.start()
        }
    }

    private func stop() {
        retry?.cancel(); retry = nil
        streamState.stop()
        updates?.cancel(); updates = nil
        locationService.endSession()
        SupportDiagnostics.shared.record("monitoring", ["monitoring": "off"])
        failure = nil; lastFixAt = nil
    }

    func refreshAuthorization() {
        defer { SupportDiagnostics.shared.record("permission", supportState) }
        authorization = locationService.authorization
        precise = locationService.precise
    }

    func status(at now: Date) -> String {
        guard enabled else { return "Off" }
        if authorization == .denied || authorization == .restricted { return "Location access needed" }
        if !precise { return "Precise Location needed" }
        if authorization != .authorizedAlways { return "Allow Always location access" }
        if store.snapshot == nil { return "Camera database needed" }
        if let failure { return failure }
        // A system-confirmed stationary pause deliberately has no fresh fixes.
        if stationary { return "Ready · waiting for movement" }
        guard let lastFixAt, now.timeIntervalSince(lastFixAt) <= 30 else { return "Waiting for location" }
        return "Monitoring"
    }

    private func receive(_ update: MonitoringLocationUpdate, sessionID: UUID) {
        refreshAuthorization()
        streamState.receive(stationary: update.stationary, at: now(), session: sessionID)
#if DEBUG
        Logger(subsystem: "xyz.dustwave.fine-me-not", category: "Location").notice(
            "Live update: stationary=\(update.stationary), hasFix=\(update.location != nil)")
#endif
        // Lifecycle events always precede accuracy filtering; a coarse first
        // resumed fix must not keep the app in its stationary state.
        if let problem = update.problem { failure = problem.message; return }
        failure = nil
        if let location = update.location { consume(location, sessionID: sessionID) }
    }

    private func consume(_ location: CLLocation, sessionID: UUID? = nil) {
        defer { SupportDiagnostics.shared.record("match", supportState) }
        let now = now()
        lastReceivedAt = location.timestamp
        lastAccuracy = location.horizontalAccuracy
        lastReportedSpeed = location.speed
        lastSpeedAccuracy = location.speedAccuracy
        let fix = LocationFix(coordinate: Coordinate(location.coordinate.latitude, location.coordinate.longitude),
                              timestamp: location.timestamp, accuracy: location.horizontalAccuracy,
                              speed: location.speed,
                              course: location.courseAccuracy >= 0 && location.courseAccuracy <= 45 ? location.course : nil,
                              speedAccuracy: location.speedAccuracy)
        let usable = precise && fix.isUsable(at: now)
#if DEBUG
        Logger(subsystem: "xyz.dustwave.fine-me-not", category: "Location").notice(
            "Location fix: usable=\(usable), accuracy=\(location.horizontalAccuracy), age=\(now.timeIntervalSince(location.timestamp))")
#endif
        if let sessionID {
            streamState.recordFix(accuracy: location.horizontalAccuracy, usable: usable, at: now, session: sessionID)
        }
        guard precise else { fixStatus = "Rejected: Precise Location is off"; return }
        guard usable else {
            fixStatus = "Rejected: location must be within 75 m accuracy and 15 seconds old"
            return
        }
        failure = nil; lastFixAt = location.timestamp; fixStatus = "Accepted"
        retry?.cancel(); retry = nil
        let previousEncounters = engine.encounters
        let warnings = engine.evaluate(fix, index: store.index, now: now, quietBelowSpeedLimit: quietBelowSpeedLimit)
        if !warnings.isEmpty {
            presenter.present(warnings)
            warningCount += warnings.count
        }
        if previousEncounters != engine.encounters,
           let data = try? JSONEncoder().encode(engine.encounters) { defaults.set(data, forKey: "warnings.encounters") }
        if store.isDue { Task { await store.refresh(force: false) } }
    }

    private func recoveryFailed(_ code: CLError.Code?) {
        guard enabled else { return }
        if code == .locationUnknown {
            if !isTracking { failure = "Location temporarily unavailable" }
        } else if code == .denied {
            refreshAuthorization()
            if authorization == .denied || authorization == .restricted { stop() }
        } else if !isTracking {
            failure = "Location failed. Retrying automatically."
            scheduleRetry()
        }
    }
}
