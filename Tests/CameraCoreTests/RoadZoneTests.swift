import Foundation
import Testing
@testable import CameraCore

private let now = ISO8601DateFormatter().date(from: "2026-09-27T18:00:00Z")!
private let path = [Coordinate(35, -106), Coordinate(35.01, -106)]
private func zone(_ geometry: [Coordinate] = path, start: Double = 600, end: Double = 600,
                  alternatives: [RoadZone.Alternative] = [], expired: Bool = false) -> RoadZone {
    RoadZone(geometry: geometry, startMeters: start, endMeters: end,
             alternatives: alternatives, sourceIDs: ["fixture/road"],
             verifiedAt: now.addingTimeInterval(-86400), validUntil: now.addingTimeInterval(expired ? -1 : 86400))
}
private func fix(_ lat: Double, _ lon: Double = -106, seconds: Double = 0,
                 course: Double? = 0, speed: Double = 20, accuracy: Double = 5, at date: Date = now) -> LocationFix {
    LocationFix(coordinate: Coordinate(lat, lon), timestamp: date.addingTimeInterval(seconds), accuracy: accuracy,
                speed: speed, course: course, speedAccuracy: 0.5)
}
private func camera(_ road: RoadZone?) -> Camera {
    Camera(id: "generic", label: "Any monitored road", kind: .speed,
           geometry: [Coordinate(35.0054, -106)], travelBearing: 0,
           sourceIDs: ["fixture/camera"], evidence: "Test fixture", roadZone: road)
}

@Test func roadZoneSeparatesLateralDistanceFromSpeedLookAhead() {
    let z = zone()
    #expect(z.assess(fix(35.003), course: 0, history: [], lead: 300).reason == .warning)
    #expect(z.assess(fix(35.003, -105.997, speed: 40), course: 0, history: [], lead: 600).reason == .outsideRoad)
    #expect(z.assess(fix(35.003, -105.99985), course: 0, history: [], lead: 300).reason == .warning)
    #expect(z.assess(fix(35.003, accuracy: 60), course: 0, history: [], lead: 300).reason == .ambiguousRoad)
    #expect(z.assess(fix(35.003), course: 180, history: [], lead: 300).reason == .oppositeDirection)
    #expect(z.assess(fix(35.006), course: 0, history: [], lead: 300).reason == .behind)
}

@Test func shorterApproachesStillWarnEarlyAndRejectAdjacentOrOppositeTravel() throws {
    let road = zone([Coordinate(35, -106), Coordinate(35.004, -106)], start: 350, end: 350)
    for kind in [CameraKind.speed, .possibleSpeed, .redLight, .speedAndRedLight] {
        let c = Camera(id: "short", label: "Short sourced approach", kind: kind,
            geometry: [Coordinate(35.00315, -106)], travelBearing: 0,
            sourceIDs: ["fixture"], evidence: "Fixture", roadZone: road)
        let index = CameraIndex(cameras: [c])
        var engine = AlertEngine()
        #expect(engine.evaluate(fix(35, speed: 50 * 0.44704), index: index, now: now).isEmpty)
        let warnings = engine.evaluate(fix(35.0002, seconds: 1, speed: 50 * 0.44704),
            index: index, now: now.addingTimeInterval(1))
        let warning = try #require(warnings.first)
        #expect((300...335).contains(warning.distance))
        for sample in [fix(35.0002, -105.999, speed: 50 * 0.44704),
                       fix(35.0002, course: 180, speed: 50 * 0.44704)] {
            var wrongRoad = AlertEngine()
            #expect(wrongRoad.evaluate(sample, index: index, now: now).isEmpty)
        }
    }
}

@Test func curvedApproachUsesRoadDistanceAndLocalDirection() {
    let curved = [Coordinate(35,-106),Coordinate(35.005,-106),Coordinate(35.005,-105.995),Coordinate(35,-105.995)]
    let z = zone(curved, start: Geometry.length(curved), end: Geometry.length(curved))
    #expect(z.assess(fix(35,-106), course: 0, history: [], lead: 600).reason == .tooFar)
    #expect(z.assess(fix(35.002,-105.995), course: 180, history: [], lead: 300).reason == .warning)
}

@Test func parallelRoadAndOverlappingCrossingNeedRoadEvidence() {
    let parallel = RoadZone.Alternative(geometry: [Coordinate(35,-105.9998),Coordinate(35.01,-105.9998)])
    let z = zone(alternatives: [parallel])
    #expect(z.assess(fix(35.004,-105.9998), course: 0, history: [], lead: 300).reason == .outsideRoad)
    #expect(z.assess(fix(35.004), course: 0, history: [], lead: 300).reason == .warning)
    let converging = RoadZone.Alternative(geometry: [Coordinate(35,-105.998),Coordinate(35.004,-106),Coordinate(35.006,-106)])
    let crossing = zone(alternatives: [converging])
    let current = fix(35.0045, seconds: 5)
    #expect(crossing.assess(current, course: 0, history: [], lead: 300).reason == .ambiguousRoad)
    #expect(crossing.assess(current, course: 0, history: [fix(35.0035)], lead: 300).reason == .warning)
    #expect(crossing.assess(current, course: 0, history: [fix(35.0035),fix(35.003,-105.9995,seconds:2)], lead: 300).reason == .ambiguousRoad)
    #expect(crossing.assess(fix(35.0045, seconds: 20), course: 0, history: [fix(35.0035)], lead: 300).reason == .ambiguousRoad)
}

@Test func turnsIntoRoadCanWarnWithMissingOrOverdueZone() {
    var engine = AlertEngine(); let index = CameraIndex(cameras: [camera(zone())])
    #expect(engine.evaluate(fix(35.004,-105.999, course: 270), index: index, now: now).isEmpty)
    #expect(engine.evaluate(fix(35.004, seconds: 3), index: index, now: now.addingTimeInterval(3)).count == 1)
    for z in [nil, zone(expired: true)] as [RoadZone?] {
        var old = AlertEngine()
        #expect(old.evaluate(fix(35.003), index: CameraIndex(cameras: [camera(z)]), now: now).count == 1)
    }
}

@Test func roadZoneEncounterStillWarnsAfterAccelerationAndRearmsOnReturn() {
    let limit = SpeedLimit(value: 45, unit: "mph", sourceID: "fixture", verifiedAt: now.addingTimeInterval(-100), validUntil: now.addingTimeInterval(1000))
    let c = Camera(id: "speed", label: "Area", kind: .possibleSpeed,
                   geometry: [Coordinate(35.004,-106),Coordinate(35.005,-106)], travelBearing: 0,
                   sourceIDs: ["fixture"], evidence: "Fixture", speedLimit: limit, roadZone: zone(start: 440,end: 560))
    let index = CameraIndex(cameras:[c]);var engine = AlertEngine()
    #expect(engine.evaluate(fix(35.0042,speed: 15),index:index,now:now).isEmpty)
    #expect(engine.evaluate(fix(35.0044,seconds:1,speed:25),index:index,now:now.addingTimeInterval(1)).count == 1)
    #expect(engine.evaluate(fix(35.0045,seconds:2,speed:25),index:index,now:now.addingTimeInterval(2)).isEmpty)
    _ = engine.evaluate(fix(35.02,seconds:100),index:index,now:now.addingTimeInterval(100))
    #expect(engine.evaluate(fix(35.0042,seconds:200,speed:25),index:index,now:now.addingTimeInterval(200)).count == 1)
}

@Test func publishedMenaulRejectsHighwayAndKeepsMonitoredRoadWarning() throws {
    let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let snapshot = try CameraSnapshot.decode(Data(contentsOf: root.appending(path:"Data/Published/cameras.json")))
    let c = try #require(snapshot.cameras.first { $0.id == "abq-menaul-vassar-possible-wb" })
    let date = snapshot.generatedAt
    #expect(c.roadZone != nil)
    for mph in [55.0,65.0] {
        var engine = AlertEngine();let index = CameraIndex(cameras:[c])
        #expect(engine.evaluate(fix(35.1071565,-106.6128987,course:283.6,speed:mph*0.44704,at:date),index:index,now:date).isEmpty)
        #expect(engine.diagnostic.reason == .outsideRoad)
    }
    var engine = AlertEngine()
    #expect(engine.evaluate(fix(35.1092749,-106.6159018,course:270,speed:25,at:date),index:CameraIndex(cameras:[c]),now:date).count == 1)
}

@Test(arguments: ["cameras.json", "cameras-2026-09-21-dc315dfa720e-79004776.json"])
func everyPublishedZoneHasUsableApproachAndRejectsOffsetTraffic(filename: String) throws {
    let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let snapshot = try CameraSnapshot.decode(Data(contentsOf: root.appending(path:"Data/Published/\(filename)")))
    try snapshot.validate(now: snapshot.generatedAt)
    let zoned = snapshot.cameras.filter { $0.roadZone != nil }
    // Keep the original 54-zone corpus as a fixed regression fixture. Current
    // coverage follows source freshness/connectivity and can legitimately shrink.
    if filename == "cameras.json" {
        struct Coverage: Decodable { let eligible: Int }
        let coverage = try JSONDecoder().decode(Coverage.self, from: Data(contentsOf:
            root.appending(path: "Data/Review/road-zone-coverage.json")))
        #expect(zoned.count == coverage.eligible)
    } else {
        #expect(zoned.count == 54)
    }
    for c in zoned {
        let z = try #require(c.roadZone)
        var warned = false
        for (a,b) in zip(z.geometry,z.geometry.dropFirst()) {
            let bearing = Geometry.bearing(from:a,to:b)
            let steps = max(1,Int(ceil(Geometry.distance(a,b)/20)))
            for step in 0..<steps {
                let t = Double(step)/Double(steps)
                let p = Coordinate(a.latitude+t*(b.latitude-a.latitude),a.longitude+t*(b.longitude-a.longitude))
                let sample = fix(p.latitude,p.longitude,course:bearing,speed:25)
                let match = z.assess(sample,course:bearing,history:[],lead:375)
                if match.reason == .warning { warned = true }
                let opposite = z.assess(sample,course:(bearing+180).truncatingRemainder(dividingBy:360),history:[],lead:375)
                #expect(opposite.reason != .warning,"Wrong direction: \(c.id)")
            }
        }
        #expect(warned,"No valid approach for \(c.id)")
        let p = z.geometry[z.geometry.count/2]
        #expect(z.assess(fix(z.geometry.map(\.latitude).max()!+0.01,p.longitude),course:0,history:[],lead:600).reason != .warning)
    }
}
