import Foundation

public struct LocationFix: Sendable {
    public let coordinate: Coordinate
    public let timestamp: Date
    public let accuracy: Double
    public let speed: Double
    public let course: Double?
    public let speedAccuracy: Double?
    public init(coordinate: Coordinate, timestamp: Date, accuracy: Double, speed: Double, course: Double?, speedAccuracy: Double? = nil) {
        self.coordinate = coordinate; self.timestamp = timestamp; self.accuracy = accuracy
        self.speed = speed; self.course = course
        self.speedAccuracy = speedAccuracy
    }
    public func isUsable(at now: Date) -> Bool {
        coordinate.isValid && accuracy.isFinite && (0...75).contains(accuracy)
        && now.timeIntervalSince(timestamp) >= -5 && now.timeIntervalSince(timestamp) <= 15
    }
}

public struct CameraWarning: Sendable {
    public let camera: Camera
    public let distance: Double
}

public struct Encounter: Codable, Sendable, Equatable {
    public var lastAlert: Date
    public var armed: Bool
}

public enum MatchReason: String, Sendable {
    case invalidFix = "GPS position is stale or inaccurate"
    case outOfOrder = "Duplicate or older GPS update"
    case notMoving = "Waiting for movement"
    case noCamera = "No mapped camera within 1 km"
    case tooFar = "Camera is outside warning distance"
    case oppositeDirection = "Camera monitors another direction"
    case behind = "Camera is behind the direction of travel"
    case approachUnconfirmed = "Waiting for approach or direction evidence"
    case outsideRoad = "Position matches a different road"
    case ambiguousRoad = "Waiting for a reliable road match"
    case cooldown = "Already warned on this approach"
    case expired = "Camera record has expired"
    case belowSpeedLimit = "Quiet: reliably below the camera's posted speed limit"
    case warning = "Camera matched for a warning"
}

public struct MatchDiagnostic: Sendable {
    public var speedLimit: SpeedLimit? = nil
    public let reason: MatchReason
    public let cameraLabel: String?
    public let distance: Double?
    public let speed: Double?
    public let course: Double?
}

public struct AlertEngine: Sendable {
    public private(set) var encounters: [String: Encounter]
    private var previous: LocationFix?
    private var roadHistory: [LocationFix] = []
    private var lastMovingAt: Date?
    private var motionAnchor: LocationFix?
    private var derivedMotion: (speed: Double, bearing: Double, at: Date)?
    public private(set) var diagnostic = MatchDiagnostic(reason: .notMoving, cameraLabel: nil, distance: nil, speed: nil, course: nil)
    public init(encounters: [String: Encounter] = [:]) { self.encounters = encounters }

    public mutating func evaluate(_ fix: LocationFix, index: CameraIndex, now: Date,
                                 quietBelowSpeedLimit: Bool = true) -> [CameraWarning] {
        guard fix.isUsable(at: now) else {
            diagnostic = MatchDiagnostic(reason: .invalidFix, cameraLabel: nil, distance: nil, speed: nil, course: nil)
            return []
        }
        if let previous, fix.timestamp <= previous.timestamp {
            diagnostic = MatchDiagnostic(reason: .outOfOrder, cameraLabel: nil, distance: nil, speed: nil, course: nil)
            return []
        }
        defer {
            previous = fix
            roadHistory = Array((roadHistory + [fix]).filter {
                fix.timestamp.timeIntervalSince($0.timestamp) <= 10
            }.suffix(16))
        }
        let motion = travelMotion(for: fix)
        if let speed = motion.speed, speed >= 2.5 { lastMovingAt = now }
        let moving = lastMovingAt.map { now.timeIntervalSince($0) < 120 } ?? false
        // Rearm even when a site is no longer in the spatial query.
        for (id, encounter) in encounters where !encounter.armed {
            guard let camera = index.camera(id: id) else { continue }
            let d = Geometry.distance(fix.coordinate, Geometry.nearest(to: fix.coordinate, on: camera.geometry))
            if d > 850 && now.timeIntervalSince(encounter.lastAlert) >= 60 { encounters[id]?.armed = true }
        }
        let candidates = index.nearby(fix.coordinate).map { camera in
            let nearest = Geometry.nearest(to: fix.coordinate, on: camera.geometry)
            return (camera: camera, point: nearest, distance: Geometry.distance(fix.coordinate, nearest))
        }.filter { $0.distance <= 1000 }.sorted { $0.distance < $1.distance }
        let closest = candidates.first
        diagnostic = MatchDiagnostic(reason: moving ? .noCamera : .notMoving, cameraLabel: closest?.camera.label,
                                     distance: closest?.distance, speed: motion.speed, course: motion.course)
        guard moving else { return [] }
        let speed = motion.speed ?? 0
        let lead = min(600, max(150, speed * 15))
        let course = motion.course
        var warnings: [CameraWarning] = []
        for (offset, candidate) in candidates.enumerated() {
            let camera = candidate.camera, nearest = candidate.point
            var distance = candidate.distance
            var reason: MatchReason = .warning
            if let end = camera.validUntil, now >= end { reason = .expired }
            else if let encounter = encounters[camera.id], !encounter.armed { reason = .cooldown }
            else if let zone = camera.roadZone, zone.isCurrent(at: now) {
                let assessment = zone.assess(fix, course: course, history: roadHistory, lead: lead)
                reason = assessment.reason; distance = assessment.distance
            }
            else if distance > lead { reason = .tooFar }
            else if let expected = camera.travelBearing, let course,
                    Geometry.angleDifference(expected, course) > 65 { reason = .oppositeDirection }
            // A good course rejects cameras behind the driver. Near a point or
            // inside a corridor, bearing-to-point is unstable and is not used.
            else if distance > max(50, fix.accuracy), let course,
                    Geometry.angleDifference(course, Geometry.bearing(from: fix.coordinate, to: nearest)) > 75 { reason = .behind }
            else if course == nil && distance > 100 {
                if let previous, fix.timestamp.timeIntervalSince(previous.timestamp) < 30 {
                    let oldDistance = Geometry.distance(previous.coordinate, Geometry.nearest(to: previous.coordinate, on: camera.geometry))
                    if oldDistance - distance <= 4 { reason = .approachUnconfirmed }
                } else { reason = .approachUnconfirmed }
            }
            if reason == .warning && quietBelowSpeedLimit && SpeedCheck.shouldSuppress(camera, fix: fix, now: now) {
                reason = .belowSpeedLimit
            }
            if offset == 0 || (reason == .warning && warnings.isEmpty) {
                diagnostic = MatchDiagnostic(speedLimit: camera.speedLimit, reason: reason, cameraLabel: camera.label, distance: distance,
                                             speed: motion.speed, course: course)
            }
            guard reason == .warning else { continue }
            warnings.append(CameraWarning(camera: camera, distance: distance))
            encounters[camera.id] = Encounter(lastAlert: now, armed: false)
        }
        // Retain a stopped encounter for up to a month so waiting at a light or
        // restarting the process does not repeat a warning.
        encounters = encounters.filter { now.timeIntervalSince($0.value.lastAlert) < 30 * 86400 }
        return warnings.sorted { $0.distance < $1.distance }
    }

    private mutating func travelMotion(for fix: LocationFix) -> (speed: Double?, course: Double?) {
        // Speed and course can independently be unavailable. Use the same
        // displacement evidence for both, before applying the movement gate.
        if let anchor = motionAnchor, fix.timestamp.timeIntervalSince(anchor.timestamp) <= 15 {
            let elapsed = fix.timestamp.timeIntervalSince(anchor.timestamp)
            let distance = Geometry.distance(anchor.coordinate, fix.coordinate)
            if elapsed >= 1 && distance >= max(20, anchor.accuracy + fix.accuracy) * 1.5 {
                let speed = distance / elapsed
                derivedMotion = (2.5...90).contains(speed)
                    ? (speed, Geometry.bearing(from: anchor.coordinate, to: fix.coordinate), fix.timestamp) : nil
                motionAnchor = fix
            }
        } else { motionAnchor = fix; derivedMotion = nil }
        let recent = derivedMotion.flatMap { fix.timestamp.timeIntervalSince($0.at) <= 5 ? $0 : nil }
        let speed = fix.speed.isFinite && fix.speed >= 0 ? fix.speed : recent?.speed
        let course = fix.course.flatMap { $0.isFinite && (0..<360).contains($0) ? $0 : nil } ?? recent?.bearing
        return (speed, course)
    }
}
