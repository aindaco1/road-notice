import XCTest
import UserNotifications
import CameraCore
@testable import FineMeNot

@MainActor
final class AlertHistoryTests: XCTestCase {
    private func directory() throws -> URL {
        let url = FileManager.default.temporaryDirectory.appending(path: UUID().uuidString)
        try FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        addTeardownBlock { try? FileManager.default.removeItem(at: url) }
        return url
    }

    private func warnings(quiet: Bool = false, date: Date = .now) -> [CameraWarning] {
        let limit = SpeedLimit(value: 45, unit: "mph", sourceID: "fixture", verifiedAt: date - 60, validUntil: date + 86400)
        let camera = Camera(id: "fixture-nb", label: "Fixture road · NB", kind: .speed,
                            geometry: [Coordinate(35.001, -106)], travelBearing: 0, speedLimit: limit)
        var engine = AlertEngine()
        return engine.evaluate(LocationFix(coordinate: Coordinate(35, -106), timestamp: date,
            accuracy: 5, speed: 10, course: 0, speedAccuracy: 0.5),
            index: CameraIndex(cameras: [camera]), now: date, quietBelowSpeedLimit: quiet)
    }

    func testPostedNotificationPersistsOnceAndTapRestoresExactEntry() async throws {
        let root = try directory()
        let history = AlertHistory(supportDirectory: root)
        var requests: [UNNotificationRequest] = []
        let presenter = AlertPresenter(history: history, sendNotification: { request in
            requests.append(request)
            return true
        })
        presenter.present(warnings())
        for _ in 0..<100 where history.entries.isEmpty { try await Task.sleep(for: .milliseconds(10)) }
        let entry = try XCTUnwrap(history.entries.first)
        let request = try XCTUnwrap(requests.first)
        XCTAssertEqual(request.content.interruptionLevel, .timeSensitive)
        XCTAssertEqual(request.identifier, entry.id.uuidString)
        XCTAssertEqual(AlertLogEntry.decode(request.content.userInfo[AlertLogEntry.payloadKey] as? String), entry)
        let relaunched = AlertHistory(supportDirectory: root)
        XCTAssertEqual(relaunched.entries, [entry])
        relaunched.open(entry)
        relaunched.record(entry) // Foreground callback and posting completion may both arrive.
        XCTAssertEqual(relaunched.entries.count, 1)
        XCTAssertEqual(relaunched.path, [entry.id])
        XCTAssertTrue(relaunched.isPresented)
        XCTAssertEqual(entry.cameras.first?.kind, .speed)
        let folder = root.appending(path: "AlertHistory")
        XCTAssertEqual(try folder.resourceValues(forKeys: [.isExcludedFromBackupKey]).isExcludedFromBackup, true)
        // Simulator uses the Mac filesystem and does not implement iOS Data Protection.
        #if !targetEnvironment(simulator)
        let attributes = try FileManager.default.attributesOfItem(atPath: folder.appending(path: "alerts.json").path)
        XCTAssertEqual(attributes[.protectionKey] as? FileProtectionType, .completeUntilFirstUserAuthentication)
        #endif
    }

    func testLimitSnapshotAndBuild16EntriesRemainReadable() throws {
        let entry = AlertLogEntry(warnings: warnings())
        let restored = try XCTUnwrap(AlertLogEntry.decode(entry.payload))
        XCTAssertEqual(restored.cameras.first?.speedLimit?.value, 45)
        XCTAssertEqual(restored.cameras.first?.speedLimit?.unit, "mph")
        var legacy = try XCTUnwrap(JSONSerialization.jsonObject(with: JSONEncoder().encode(entry)) as? [String: Any])
        var cameras = try XCTUnwrap(legacy["cameras"] as? [[String: Any]])
        for index in cameras.indices { cameras[index].removeValue(forKey: "speedLimit") }
        legacy["cameras"] = cameras
        let data = try JSONSerialization.data(withJSONObject: legacy)
        let oldEntry = try XCTUnwrap(AlertLogEntry.decode(String(data: data, encoding: .utf8)))
        XCTAssertEqual(oldEntry.id, entry.id)
        XCTAssertNil(oldEntry.cameras.first?.speedLimit)
        let root = try directory()
        let history = AlertHistory(supportDirectory: root)
        history.record(oldEntry)
        XCTAssertEqual(AlertHistory(supportDirectory: root).entries, [oldEntry])
    }

    func testDeniedAndFailedNotificationRequestsDoNotLog() async throws {
        for fails in [false, true] {
            let history = AlertHistory(supportDirectory: try directory())
            let presenter = AlertPresenter(history: history, sendNotification: { _ in
                if fails { throw CocoaError(.fileWriteUnknown) }
                return false
            })
            let entry = AlertLogEntry(warnings: warnings())
            await presenter.postNotification(UNNotificationRequest(identifier: entry.id.uuidString,
                content: UNMutableNotificationContent(), trigger: nil), entry: entry)
            XCTAssertTrue(history.entries.isEmpty)
        }
    }

    func testQuietApproachDoesNotPostOrLog() async throws {
        let history = AlertHistory(supportDirectory: try directory())
        let presenter = AlertPresenter(history: history, sendNotification: { _ in
            XCTFail("Suppressed approach must not post a notification")
            return true
        })
        let suppressed = warnings(quiet: true)
        XCTAssertTrue(suppressed.isEmpty)
        presenter.present(suppressed)
        await Task.yield()
        XCTAssertTrue(history.entries.isEmpty)
    }

    func testNewestFirstRetentionClearAndColdTapRecovery() throws {
        let root = try directory()
        let history = AlertHistory(supportDirectory: root)
        let now = Date.now
        let first = AlertLogEntry(warnings: warnings(), date: now)
        history.record(first)
        for index in 1...AlertHistory.capacity {
            history.record(AlertLogEntry(warnings: warnings(), date: now + Double(index)))
        }
        XCTAssertEqual(history.entries.count, AlertHistory.capacity)
        XCTAssertFalse(history.entries.contains(first))
        XCTAssertEqual(history.entries.first?.date, now + Double(AlertHistory.capacity))
        history.open(first)
        XCTAssertTrue(history.entries.contains(first))
        XCTAssertEqual(history.entries.count, AlertHistory.capacity)
        history.clear()
        XCTAssertTrue(AlertHistory(supportDirectory: root).entries.isEmpty)
        // An existing notification payload can recover its item after a terminated launch.
        let recovered = AlertHistory(supportDirectory: root)
        recovered.open(try XCTUnwrap(AlertLogEntry.decode(first.payload)))
        XCTAssertEqual(recovered.path, [first.id])
        XCTAssertEqual(recovered.entries, [first])
        XCTAssertNil(AlertLogEntry.decode("invalid"))
        XCTAssertNil(AlertLogEntry.decode(nil))
    }
}
