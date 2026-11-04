import Foundation
import Testing
@testable import CameraCore

private let incident = ISO8601DateFormatter().date(from: "2026-10-28T15:41:49Z")!
private func releasedCameras() throws -> [Camera] {
    let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    return try CameraSnapshot.decode(Data(contentsOf: root.appending(path:
        "Data/Published/cameras-2026-09-28-161eb14e875c-1f615099.json"))).cameras
}

@Test func currentIncidentZonesProvideFullLeadAndStayActiveOffline() throws {
    let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let snapshot = try CameraSnapshot.decode(Data(contentsOf: root.appending(path: "Data/Published/cameras.json")))
    let ids = ["abq-menaul-vassar-possible-wb", "abq-coors-st-joseph-possible-nb", "abq-coors-st-joseph-possible-sb"]
    let later = snapshot.generatedAt.addingTimeInterval(180 * 86400)
    for id in ids {
        let camera = try #require(snapshot.cameras.first { $0.id == id })
        let zone = try #require(camera.roadZone)
        #expect(zone.startMeters >= 600)
        let index = CameraIndex(cameras: [camera])
        var engine = AlertEngine()
        #expect(engine.evaluate(observed(camera.geometry[5], at: later, course: camera.travelBearing),
            index: index, now: later).count == 1)
        if id.contains("vassar") {
            var highway = AlertEngine()
            #expect(highway.evaluate(observed(Coordinate(35.1071565, -106.6128987), at: later,
                mph: 65, course: 283.6), index: index, now: later).isEmpty)
        }
    }
}
private func observed(_ point: Coordinate, at: Date = incident, mph: Double = 50, course: Double?) -> LocationFix {
    LocationFix(coordinate: point, timestamp: at, accuracy: 5, speed: mph * 0.44704,
                course: course, speedAccuracy: 0.5)
}

@Test func overdueMenaulZoneStillRejectsHighwayAndAllowsCorrectRoad() throws {
    let camera = try #require(releasedCameras().first { $0.id == "abq-menaul-vassar-possible-wb" })
    let index = CameraIndex(cameras: [camera])
    // Includes an offline phone months after its last database download.
    for date in [incident, incident.addingTimeInterval(180 * 86400)] {
        for mph in [55.0, 65.0] {
            var engine = AlertEngine()
            #expect(engine.evaluate(observed(Coordinate(35.1071565, -106.6128987), at: date,
                mph: mph, course: 283.6), index: index, now: date).isEmpty)
            #expect(engine.diagnostic.reason == .outsideRoad)
        }
        var engine = AlertEngine()
        #expect(engine.evaluate(observed(camera.geometry[2], at: date, course: 270),
            index: index, now: date).count == 1)
        var opposite = AlertEngine()
        #expect(opposite.evaluate(observed(camera.geometry[2], at: date, course: 90),
            index: index, now: date).isEmpty)
    }
}

@Test func coorsDirectionDropoutCannotWarnForOpposingApproach() throws {
    let cameras = try releasedCameras().filter { $0.id.hasPrefix("abq-coors-st-joseph-") }
    for zoned in [true, false] {
        let index = CameraIndex(cameras: cameras.map { c in
            Camera(id: c.id, siteID: c.siteID, label: c.label, kind: c.kind,
                geometry: c.geometry, travelBearing: c.travelBearing, sourceIDs: c.sourceIDs,
                speedLimit: c.speedLimit, roadZone: zoned ? c.roadZone : nil)
        })
        for camera in cameras {
            let bearing = try #require(camera.travelBearing)
            let point = camera.geometry[5]
            var engine = AlertEngine()
            let first = engine.evaluate(observed(point, course: bearing), index: index, now: incident)
            #expect(first.map(\.camera.id) == [camera.id])
            let next = Coordinate(point.latitude + (bearing == 0 ? 0.000177 : -0.000177), point.longitude)
            let date = incident.addingTimeInterval(1)
            #expect(engine.evaluate(observed(next, at: date, course: nil), index: index, now: date).isEmpty)
            var cold = AlertEngine()
            #expect(cold.evaluate(observed(point, course: nil), index: index, now: incident).isEmpty)
        }
    }
}

@Test func quietIsInclusiveAtTheLimitAndDoesNotConsumeEncounter() {
    let limit = SpeedLimit(value: 45, unit: "mph", sourceID: "fixture",
        verifiedAt: incident.addingTimeInterval(-86400), validUntil: incident.addingTimeInterval(86400))
    let camera = Camera(id: "limit", label: "Limit", kind: .speed,
        geometry: [Coordinate(35.001, -106)], travelBearing: 0, speedLimit: limit)
    let index = CameraIndex(cameras: [camera])
    var engine = AlertEngine()
    for (second, mph) in [40.0, 44.0, 45.0, 45.01].enumerated() {
        let date = incident.addingTimeInterval(Double(second))
        let warnings = engine.evaluate(observed(Coordinate(35, -106), at: date, mph: mph, course: 0),
            index: index, now: date)
        #expect(warnings.count == (mph > 45 ? 1 : 0))
        if mph <= 45 { #expect(engine.encounters.isEmpty) }
    }
}
