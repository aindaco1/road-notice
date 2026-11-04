import Foundation
import Testing
@testable import CameraCore

private let start = Date(timeIntervalSince1970: 1_789_430_400)
private func camera(_ id: String = "abq-1", bearing: Double? = 0, kind: CameraKind = .speed,
                    geometry: [Coordinate] = [Coordinate(35.003, -106)]) -> Camera {
    Camera(id: id, label: "Test road", kind: kind, geometry: geometry, travelBearing: bearing,
           sourceIDs: ["test"], evidence: "Fixture")
}
private func fix(_ latitude: Double, lon: Double = -106, seconds: Double = 0, course: Double? = 0,
                 speed: Double = 20, accuracy: Double = 5, at date: Date = start) -> LocationFix {
    LocationFix(coordinate: Coordinate(latitude, lon), timestamp: date.addingTimeInterval(seconds),
                accuracy: accuracy, speed: speed, course: course)
}

@Test func warnsOnceAndRearmsAfterLeaving() {
    let index = CameraIndex(cameras: [camera()]); var engine = AlertEngine()
    #expect(engine.evaluate(fix(35.0005), index: index, now: start).count == 1)
    #expect(engine.evaluate(fix(35.001, seconds: 5), index: index, now: start.addingTimeInterval(5)).isEmpty)
    #expect(engine.evaluate(fix(35.003, seconds: 70, speed: 0), index: index, now: start.addingTimeInterval(70)).isEmpty)
    #expect(engine.evaluate(fix(35.02, seconds: 130), index: index, now: start.addingTimeInterval(130)).isEmpty)
    #expect(engine.evaluate(fix(35.0005, seconds: 200), index: index, now: start.addingTimeInterval(200)).count == 1)
}

@Test func rejectsOppositeDirectionAndCameraBehind() {
    var engine = AlertEngine()
    let index = CameraIndex(cameras: [camera(), camera("opposite", bearing: 180)])
    #expect(engine.evaluate(fix(35.0005), index: index, now: start).map(\.camera.id) == ["abq-1"])
    var behind = AlertEngine()
    #expect(behind.evaluate(fix(35.005), index: CameraIndex(cameras: [camera(bearing: nil)]), now: start).isEmpty)
}

@Test func rejectsBadAndOldFixes() {
    var engine = AlertEngine(); let index = CameraIndex(cameras: [camera()])
    #expect(engine.evaluate(fix(35.001, accuracy: 100), index: index, now: start).isEmpty)
    #expect(engine.evaluate(fix(35.001), index: index, now: start.addingTimeInterval(30)).isEmpty)
    #expect(engine.evaluate(fix(35.001, speed: 0), index: index, now: start).isEmpty)
}

@Test func restartAndDatabaseCorrectionPreserveCooldown() throws {
    var engine = AlertEngine(); let index = CameraIndex(cameras: [camera()])
    #expect(engine.evaluate(fix(35.001), index: index, now: start).count == 1)
    let restored = try JSONDecoder().decode([String: Encounter].self, from: JSONEncoder().encode(engine.encounters))
    var relaunched = AlertEngine(encounters: restored)
    let corrected = CameraIndex(cameras: [camera(geometry: [Coordinate(35.0031, -106)])])
    #expect(relaunched.evaluate(fix(35.001, seconds: 5), index: corrected, now: start.addingTimeInterval(5)).isEmpty)
}

@Test func longMobileCorridorIsIndexedAtItsMiddle() {
    let mobile = camera(bearing: nil, kind: .possibleSpeed, geometry: [Coordinate(35, -106), Coordinate(35.1, -106)])
    let index = CameraIndex(cameras: [mobile]); var engine = AlertEngine()
    #expect(index.nearby(Coordinate(35.05, -106)).count == 1)
    #expect(engine.evaluate(fix(35.05), index: index, now: start).first?.camera.kind == .possibleSpeed)
    #expect(engine.evaluate(fix(35.055, seconds: 90), index: index, now: start.addingTimeInterval(90)).isEmpty)
}

@Test func expiredMobileSiteDoesNotWarn() {
    let c = Camera(id: "expired", label: "Site", kind: .possibleSpeed, geometry: [Coordinate(35.003, -106)], validUntil: start)
    var engine = AlertEngine()
    #expect(engine.evaluate(fix(35.001), index: CameraIndex(cameras: [c]), now: start).isEmpty)
}

@Test func unknownCourseNeedsApproachEvidence() {
    var engine = AlertEngine(); let index = CameraIndex(cameras: [camera(bearing: nil)])
    #expect(engine.evaluate(fix(35.0005, course: nil), index: index, now: start).isEmpty)
    #expect(engine.evaluate(fix(35.001, seconds: 5, course: nil), index: index, now: start.addingTimeInterval(5)).count == 1)
}

@Test func denverMidnightFollowsDaylightSaving() {
    let parse = ISO8601DateFormatter()
    for (date, expected) in [("2026-03-08T18:00:00Z", "2026-03-09T06:00:00Z"),
                             ("2026-11-01T18:00:00Z", "2026-11-02T07:00:00Z")] {
        #expect(UpdateSchedule.nextRefresh(after: parse.date(from: date)!) == parse.date(from: expected)!)
    }
    let monday = parse.date(from: "2026-09-14T06:00:00Z")!
    #expect(UpdateSchedule.currentWeekStart(at: monday) == monday)
    #expect(!UpdateSchedule.isDue(generatedAt: monday, now: monday))
    #expect(UpdateSchedule.isDue(generatedAt: monday.addingTimeInterval(-1), now: monday))
}

@Test func infersTravelDirectionWhenCourseAccuracyIsUnavailable() {
    var engine = AlertEngine()
    let index = CameraIndex(cameras: [camera(), camera("opposite", bearing: 180)])
    #expect(engine.evaluate(fix(35, course: nil), index: index, now: start).isEmpty)
    let warnings = engine.evaluate(fix(35.0005, seconds: 3, course: nil), index: index, now: start.addingTimeInterval(3))
    #expect(warnings.map(\.camera.id) == ["abq-1"])
}

@Test func movingWithoutReportedSpeedStillWarns() {
    var engine = AlertEngine()
    let index = CameraIndex(cameras: [camera(), camera("opposite", bearing: 180)])
    #expect(engine.evaluate(fix(35, course: nil, speed: -1), index: index, now: start).isEmpty)
    let warnings = engine.evaluate(fix(35.0005, seconds: 3, course: nil, speed: -1),
                                   index: index, now: start.addingTimeInterval(3))
    #expect(warnings.map(\.camera.id) == ["abq-1"])
    #expect(engine.diagnostic.reason == .warning)
    #expect((engine.diagnostic.speed ?? 0) > 10)
}

@Test func unavailableSpeedDoesNotTurnJitterOrAnOldAnchorIntoMovement() {
    let index = CameraIndex(cameras: [camera()])
    var engine = AlertEngine()
    for (latitude, seconds) in [(35.001, 0.0), (35.00105, 3.0), (35.00098, 6.0), (35.0015, 30.0)] {
        #expect(engine.evaluate(fix(latitude, seconds: seconds, course: nil, speed: -1),
                                index: index, now: start.addingTimeInterval(seconds)).isEmpty)
    }
    #expect(engine.diagnostic.reason == .notMoving)
    var jump = AlertEngine()
    _ = jump.evaluate(fix(34.999, course: nil, speed: -1), index: index, now: start)
    #expect(jump.evaluate(fix(35.001, seconds: 1, course: nil, speed: -1),
                          index: index, now: start.addingTimeInterval(1)).isEmpty)
}

@Test func diagnosticDistinguishesMissingDataFromWrongDirection() {
    var engine = AlertEngine()
    _ = engine.evaluate(fix(35.001), index: CameraIndex(cameras: []), now: start)
    #expect(engine.diagnostic.reason == .noCamera)
    _ = engine.evaluate(fix(35.001, seconds: 1), index: CameraIndex(cameras: [camera(bearing: 180)]), now: start.addingTimeInterval(1))
    #expect(engine.diagnostic.reason == .oppositeDirection)
}

@Test func publishedSnapshotDecodesAndIndexesEveryMetroCorridor() throws {
    let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let snapshot = try CameraSnapshot.decode(Data(contentsOf: root.appending(path: "Data/Published/cameras.json")))
    try snapshot.validate()
    let index = CameraIndex(cameras: snapshot.cameras)
    let corridors = snapshot.cameras.filter { $0.id.hasPrefix("rr-nm528-") }
    #expect(corridors.count == 3)
    for corridor in corridors {
        #expect(corridor.kind == .possibleSpeed)
        #expect(corridor.geometry.count > 2)
        #expect(index.nearby(corridor.geometry[corridor.geometry.count / 2]).contains { $0.id == corridor.id })
    }
}

@Test func publishedCoorsAreaWarnsInBothDirectionsWithoutReportedMotion() throws {
    let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let snapshot = try CameraSnapshot.decode(Data(contentsOf: root.appending(path: "Data/Published/cameras.json")))
    let index = CameraIndex(cameras: snapshot.cameras)
    for (direction, origin, step, longitude) in [("nb", 35.124, 0.00018, -106.70156),
                                                ("sb", 35.139, -0.00018, -106.70177)] {
        var engine = AlertEngine()
        var matches: [String] = []
        for second in 0..<90 {
            let at = snapshot.generatedAt.addingTimeInterval(Double(second))
            let update = fix(origin + step * Double(second), lon: longitude, seconds: Double(second), course: nil, speed: -1, at: snapshot.generatedAt)
            matches += engine.evaluate(update, index: index, now: at).map(\.camera.id)
        }
        #expect(matches == ["abq-coors-st-joseph-possible-\(direction)"])
    }
    // Waiting at the intersection must not invent driving from stationary fixes.
    var parked = AlertEngine()
    for second in 0..<10 {
        let update = fix(35.1282, lon: -106.70156, seconds: Double(second), course: nil, speed: -1, at: snapshot.generatedAt)
        #expect(parked.evaluate(update, index: index, now: snapshot.generatedAt.addingTimeInterval(Double(second))).isEmpty)
    }
}

@Test func everyReviewedWarningAreaAlertsOnceAndRejectsOppositeTravel() throws {
    let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let snapshot = try CameraSnapshot.decode(Data(contentsOf: root.appending(path: "Data/Published/cameras.json")))
    let index = CameraIndex(cameras: snapshot.cameras)
    let areas = snapshot.cameras.filter { ($0.id.hasPrefix("abq-") || $0.id.hasPrefix("bernco-")) && $0.geometry.count > 1 }
    #expect(areas.count == 29) // 20 city areas plus nine newly reviewed county segments.
    for area in areas {
        let heading = try #require(area.travelBearing)
        // Review geometries may be stored in either order. Follow monitored travel.
        let points = Geometry.angleDifference(Geometry.bearing(from: area.geometry.first!, to: area.geometry.last!), heading) < 90
            ? area.geometry : area.geometry.reversed()
        var forward = AlertEngine(), reverse = AlertEngine()
        var matches: [String] = []
        var elapsed = 0.0
        for (a, b) in zip(points, points.dropFirst()) {
            let steps = max(1, Int(ceil(Geometry.distance(a, b) / 20)))
            for step in 0..<steps {
                let t = Double(step) / Double(steps)
                let position = Coordinate(a.latitude + (b.latitude-a.latitude)*t, a.longitude + (b.longitude-a.longitude)*t)
                let time = snapshot.generatedAt.addingTimeInterval(elapsed)
                let update = LocationFix(coordinate: position, timestamp: time, accuracy: 5, speed: 15, course: heading)
                matches += forward.evaluate(update, index: index, now: time).map(\.camera.id).filter { $0 == area.id }
                let opposite = LocationFix(coordinate: position, timestamp: time, accuracy: 5, speed: 15,
                                           course: (heading + 180).truncatingRemainder(dividingBy: 360))
                #expect(!reverse.evaluate(opposite, index: index, now: time).contains { $0.camera.id == area.id })
                elapsed += 1
            }
        }
        #expect(matches == [area.id], "Area should warn once: \(area.id)")
    }
}

@Test func reconciledEubankPointWarnsWithoutReportedSpeed() throws {
    let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let snapshot = try CameraSnapshot.decode(Data(contentsOf: root.appending(path: "Data/Published/cameras.json")))
    let camera = try #require(snapshot.cameras.first { $0.id == "abq-eubank-sierra-vista-possible-sb" })
    #expect(camera.kind == .speed)
    #expect(camera.geometry.count == 1)
    let index = CameraIndex(cameras: [camera])
    var engine = AlertEngine()
    var warned: [String] = []
    for second in 0..<60 {
        let at = snapshot.generatedAt.addingTimeInterval(Double(second))
        let update = fix(35.132 - 0.00018 * Double(second), lon: -106.53343,
                         seconds: Double(second), course: nil, speed: -1, at: snapshot.generatedAt)
        warned += engine.evaluate(update, index: index, now: at).map(\.camera.id)
    }
    #expect(warned == [camera.id])
}
