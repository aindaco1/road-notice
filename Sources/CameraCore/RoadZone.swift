import Foundation

/// A directed, source-connected road centerline. Distances locate the monitored
/// point/area along that line; look-ahead never increases the corridor's width.
public struct RoadZone: Codable, Hashable, Sendable {
    public struct Alternative: Codable, Hashable, Sendable {
        public let geometry: [Coordinate]
        public let oneWay: Bool
        public init(geometry: [Coordinate], oneWay: Bool = false) {
            self.geometry = geometry; self.oneWay = oneWay
        }
    }
    public let geometry: [Coordinate]
    public let startMeters: Double
    public let endMeters: Double
    public let halfWidthMeters: Double
    public let alternatives: [Alternative]
    public let sourceIDs: [String]
    public let verifiedAt: Date
    public let validUntil: Date

    public init(geometry: [Coordinate], startMeters: Double, endMeters: Double,
                halfWidthMeters: Double = 20, alternatives: [Alternative] = [],
                sourceIDs: [String], verifiedAt: Date, validUntil: Date) {
        self.geometry = geometry; self.startMeters = startMeters; self.endMeters = endMeters
        self.halfWidthMeters = halfWidthMeters; self.alternatives = alternatives
        self.sourceIDs = sourceIDs; self.verifiedAt = verifiedAt; self.validUntil = validUntil
    }

    public var isValid: Bool {
        func validLine(_ line: [Coordinate]) -> Bool {
            (2...2000).contains(line.count) && line.allSatisfy(\.isValid)
                && Geometry.length(line) > 0 && Geometry.length(line) < 50_000
        }
        return validLine(geometry) && startMeters.isFinite && endMeters.isFinite
            && startMeters >= 0 && endMeters >= startMeters && endMeters <= Geometry.length(geometry) + 1
            && (5...40).contains(halfWidthMeters) && !sourceIDs.isEmpty
            && alternatives.count <= 80 && alternatives.allSatisfy { validLine($0.geometry) }
            && validUntil > verifiedAt && validUntil.timeIntervalSince(verifiedAt) <= 30 * 86400
    }

    public func isCurrent(at now: Date) -> Bool { verifiedAt <= now && now < validUntil }

    public func assess(_ fix: LocationFix, course: Double?, history: [LocationFix], lead: Double) -> (reason: MatchReason, distance: Double) {
        let position = Geometry.project(fix.coordinate, onto: geometry)
        let ahead = max(0, startMeters - position.along)
        guard fix.accuracy <= 25 else { return (.ambiguousRoad, ahead) }
        let width = halfWidthMeters + min(10, fix.accuracy)
        guard position.distance <= width else { return (.outsideRoad, ahead) }
        guard let course else { return (.approachUnconfirmed, ahead) }
        guard Geometry.angleDifference(course, position.bearing) <= 60 else { return (.oppositeDirection, ahead) }
        guard position.along <= endMeters + 20 else { return (.behind, ahead) }
        guard ahead <= lead else { return (.tooFar, ahead) }
        let margin = max(5, fix.accuracy)
        for road in alternatives {
            let other = Geometry.project(fix.coordinate, onto: road.geometry)
            let angle = road.oneWay ? Geometry.angleDifference(course, other.bearing)
                : min(Geometry.angleDifference(course, other.bearing), Geometry.angleDifference(course, (other.bearing + 180).truncatingRemainder(dividingBy: 360)))
            guard angle <= 60, other.distance <= position.distance + margin else { continue }
            if other.distance + margin < position.distance { return (.outsideRoad, ahead) }
            // At an overlapping road crossing, retain a recent clearly matched
            // approach. A cold or ambiguous fix cannot choose a road by proximity.
            var established = false
            for previous in history.reversed() {
                guard previous.accuracy <= 25,
                      (0...10).contains(fix.timestamp.timeIntervalSince(previous.timestamp)) else { continue }
                let prior = Geometry.project(previous.coordinate, onto: geometry)
                let priorOther = Geometry.project(previous.coordinate, onto: road.geometry)
                let priorMargin = max(5, previous.accuracy)
                // The latest clear evidence wins, including a recent turn off
                // the monitored road. Older membership cannot override it.
                if priorOther.distance + priorMargin < prior.distance { break }
                if prior.distance <= halfWidthMeters + min(10, previous.accuracy)
                    && prior.distance + priorMargin < priorOther.distance {
                    established = true
                    break
                }
            }
            guard established else { return (.ambiguousRoad, ahead) }
        }
        return (.warning, ahead)
    }
}
