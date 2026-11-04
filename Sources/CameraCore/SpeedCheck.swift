import Foundation

/// An approved posted limit or conservative suppression bound for this approach.
/// The publisher may reduce fully known conditional limits to their minimum;
/// unresolved conditions, unknown units and expired evidence still warn.
public struct SpeedLimit: Codable, Hashable, Sendable {
    public let value: Double
    public let unit: String
    public let sourceID: String
    public let verifiedAt: Date
    public let validUntil: Date
    public let conditional: Bool

    public init(value: Double, unit: String, sourceID: String, verifiedAt: Date,
                validUntil: Date, conditional: Bool = false) {
        self.value = value; self.unit = unit; self.sourceID = sourceID
        self.verifiedAt = verifiedAt; self.validUntil = validUntil; self.conditional = conditional
    }

    public func metersPerSecond(at now: Date) -> Double? {
        guard !conditional, !sourceID.isEmpty, value.isFinite,
              verifiedAt <= now, now < validUntil,
              validUntil.timeIntervalSince(verifiedAt) <= 90 * 86400 else { return nil }
        switch unit {
        case "mph" where (5...85).contains(value): return value * 0.44704
        case "km/h" where (8...140).contains(value): return value / 3.6
        default: return nil
        }
    }
}

public enum SpeedCheck {
    public static let preferenceKey = "warnings.quietBelowSpeedLimit"
    public static func isEnabled(in defaults: UserDefaults) -> Bool {
        defaults.object(forKey: preferenceKey) as? Bool ?? true
    }

    public static func shouldSuppress(_ camera: Camera, fix: LocationFix, now: Date) -> Bool {
        guard camera.kind == .speed || camera.kind == .possibleSpeed,
              let limit = camera.speedLimit?.metersPerSecond(at: now),
              fix.isUsable(at: now), (0...3).contains(now.timeIntervalSince(fix.timestamp)),
              fix.speed.isFinite, fix.speed >= 0,
              let uncertainty = fix.speedAccuracy, uncertainty.isFinite,
              (0...2).contains(uncertainty) else { return false }
        // Accuracy gates whether the measurement is usable; it does not move
        // the posted threshold. Never quiet using displacement-derived speed.
        return fix.speed <= limit
    }
}
