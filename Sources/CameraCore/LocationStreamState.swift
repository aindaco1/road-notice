import Foundation

/// Lifetime and pause state for the single live location stream. Core Location,
/// rather than an app timer or the warning speed threshold, decides when to idle.
public struct LocationStreamState: Sendable {
    public private(set) var sessionID: UUID?
    public private(set) var stationary = false
    public private(set) var resumedAt: Date?
    public private(set) var firstResumedAccuracy: Double?
    public private(set) var resumedUsableFixDelay: TimeInterval?
    private var receivedResumedFix = false

    public init() {}
    public var isTracking: Bool { sessionID != nil }

    /// Repeated foreground/recovery starts must not create concurrent streams.
    public mutating func begin() -> UUID? {
        guard sessionID == nil else { return nil }
        let id = UUID()
        sessionID = id
        stationary = false
        resumedAt = nil
        firstResumedAccuracy = nil
        resumedUsableFixDelay = nil
        receivedResumedFix = false
        return id
    }

    public func isCurrent(_ id: UUID) -> Bool { sessionID == id }

    /// An old cancelled task must not tear down a newer monitoring session.
    @discardableResult
    public mutating func end(_ id: UUID) -> Bool {
        guard isCurrent(id) else { return false }
        stop()
        return true
    }

    public mutating func stop() {
        sessionID = nil
        stationary = false
    }

    /// Process power state even when the accompanying location is absent or too
    /// coarse for camera matching. A stationary update never ends the stream.
    public mutating func receive(stationary value: Bool, at now: Date, session id: UUID) {
        guard isCurrent(id) else { return }
        if stationary && !value {
            resumedAt = now
            firstResumedAccuracy = nil
            resumedUsableFixDelay = nil
            receivedResumedFix = false
        }
        stationary = value
    }

    /// Local diagnostic timing starts at Core Location's resumed event, not at
    /// physical departure (which the app cannot observe while suspended).
    public mutating func recordFix(accuracy: Double, usable: Bool, at now: Date, session id: UUID) {
        guard isCurrent(id), !stationary, let resumedAt else { return }
        if !receivedResumedFix {
            firstResumedAccuracy = accuracy.isFinite && accuracy >= 0 ? accuracy : nil
            receivedResumedFix = true
        }
        if usable && resumedUsableFixDelay == nil {
            resumedUsableFixDelay = max(0, now.timeIntervalSince(resumedAt))
        }
    }
}
