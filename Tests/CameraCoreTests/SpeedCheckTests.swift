import Foundation
import Testing
@testable import CameraCore

private let now = Date(timeIntervalSince1970: 1_789_430_400)
private func limit(_ value: Double = 40, unit: String = "mph", conditional: Bool = false,
                   expiry: Date = now.addingTimeInterval(30 * 86400)) -> SpeedLimit {
    SpeedLimit(value: value, unit: unit, sourceID: "agency/test/1", verifiedAt: now.addingTimeInterval(-86400), validUntil: expiry, conditional: conditional)
}
private func camera(_ kind: CameraKind = .speed, limit: SpeedLimit? = limit()) -> Camera {
    Camera(id: "test", label: "Road", kind: kind, geometry: [Coordinate(35.001, -106)], travelBearing: 0, speedLimit: limit)
}
private func fix(speed: Double = 10, uncertainty: Double? = 0.5, age: Double = 0, seconds: Double = 0) -> LocationFix {
    LocationFix(coordinate: Coordinate(35, -106), timestamp: now.addingTimeInterval(seconds-age), accuracy: 5, speed: speed, course: 0, speedAccuracy: uncertainty)
}

@Test func speedPreferenceDefaultsOnForFreshAndUpgradedInstalls() {
    let name = "speed-check-tests-\(UUID())"
    let defaults = UserDefaults(suiteName: name)!
    defer { defaults.removePersistentDomain(forName: name) }
    #expect(SpeedCheck.isEnabled(in: defaults))
    defaults.set(true, forKey: "warnings.enabled") // Existing build's saved preference.
    #expect(SpeedCheck.isEnabled(in: defaults))
    defaults.set(false, forKey: SpeedCheck.preferenceKey)
    #expect(!SpeedCheck.isEnabled(in: defaults))
}

@Test func onlySpeedWarningsCanBeQuieted() {
    #expect(SpeedCheck.shouldSuppress(camera(), fix: fix(), now: now))
    #expect(SpeedCheck.shouldSuppress(camera(.possibleSpeed), fix: fix(), now: now))
    for kind in [CameraKind.redLight, .speedAndRedLight] {
        #expect(!SpeedCheck.shouldSuppress(camera(kind), fix: fix(), now: now))
    }
}

@Test func speedUncertaintyAndUnknownsAlwaysWarn() {
    let c = camera()
    for f in [fix(speed: -1), fix(speed: .nan), fix(uncertainty: nil), fix(uncertainty: -1),
              fix(uncertainty: 2.1), fix(uncertainty: .infinity), fix(age: 4), fix(age: -1),
              fix(speed: 40 * 0.44704 + 0.01)] {
        #expect(!SpeedCheck.shouldSuppress(c, fix: f, now: now))
    }
    for l in [nil, limit(unit: "knots"), limit(conditional: true), limit(expiry: now),
              limit(0), limit(.nan), limit(expiry: now.addingTimeInterval(91 * 86400))] {
        #expect(!SpeedCheck.shouldSuppress(camera(limit: l), fix: fix(), now: now))
    }
    #expect(SpeedCheck.shouldSuppress(camera(limit: limit(60, unit: "km/h")), fix: fix(), now: now))
}

@Test func quietApproachStaysArmedAndCanWarnOnAccelerationOrToggleOff() {
    let index = CameraIndex(cameras: [camera()]); var engine = AlertEngine()
    #expect(engine.evaluate(fix(), index: index, now: now).isEmpty)
    #expect(engine.diagnostic.reason == .belowSpeedLimit)
    #expect(engine.encounters.isEmpty)
    #expect(engine.evaluate(fix(speed: 20, seconds: 1), index: index, now: now.addingTimeInterval(1)).count == 1)
    #expect(engine.evaluate(fix(speed: 20, seconds: 2), index: index, now: now.addingTimeInterval(2)).isEmpty)
    var off = AlertEngine()
    #expect(off.evaluate(fix(), index: index, now: now, quietBelowSpeedLimit: false).count == 1)
}

@Test func publishedEnrichmentDecodesInCurrentAppAndKeepsRedLightWarnings() throws {
    let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let snapshot = try CameraSnapshot.decode(Data(contentsOf: root.appending(path: "Data/Published/cameras.json")))
    try snapshot.validate(now: snapshot.generatedAt)
    for camera in snapshot.cameras {
        if let limit = camera.speedLimit {
            #expect(camera.kind == .speed || camera.kind == .possibleSpeed)
            #expect(limit.metersPerSecond(at: snapshot.generatedAt) != nil)
        }
    }
}

@Test func verifiedCoorsApproachesQuietAtOrBelow45AndWarnAboveOrWithUnknownSpeedAccuracy() throws {
    let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let snapshot = try CameraSnapshot.decode(Data(contentsOf: root.appending(path: "Data/Published/cameras-2026-09-28-161eb14e875c-1f615099.json")))
    let cameras = snapshot.cameras.filter { $0.id.hasPrefix("abq-coors-st-joseph-") }
    #expect(cameras.count == 2)
    for camera in cameras {
        #expect(camera.kind == .speed)
        #expect(camera.speedLimit?.value == 45)
        func observed(_ mph: Double, uncertainty: Double? = 0.5) -> LocationFix {
            LocationFix(coordinate: camera.geometry[0], timestamp: snapshot.generatedAt,
                accuracy: 5, speed: mph * 0.44704, course: camera.travelBearing, speedAccuracy: uncertainty)
        }
        #expect(SpeedCheck.shouldSuppress(camera, fix: observed(40), now: snapshot.generatedAt))
        #expect(SpeedCheck.shouldSuppress(camera, fix: observed(44), now: snapshot.generatedAt))
        #expect(SpeedCheck.shouldSuppress(camera, fix: observed(45), now: snapshot.generatedAt))
        #expect(!SpeedCheck.shouldSuppress(camera, fix: observed(45.01), now: snapshot.generatedAt))
        #expect(!SpeedCheck.shouldSuppress(camera, fix: observed(40, uncertainty: nil), now: snapshot.generatedAt))
    }
}
