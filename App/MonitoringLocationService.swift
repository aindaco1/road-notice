import CoreLocation
import UIKit

/// Only the operating-system boundary is replaceable. The controller consumes
/// these same events and owns the same retry/matching path in tests and the app.
struct MonitoringLocationUpdate: Sendable {
    enum Problem: Sendable {
        case authorization, precision, backgroundAccess, unavailable
        var message: String {
            switch self {
            case .authorization: "Location access needed"
            case .precision: "Precise Location needed"
            case .backgroundAccess: "Open Road Notice to restore location access"
            case .unavailable: "Location temporarily unavailable"
            }
        }
    }
    let stationary: Bool
    var location: CLLocation? = nil
    var problem: Problem? = nil

    init(stationary: Bool, location: CLLocation? = nil, problem: Problem? = nil) {
        self.stationary = stationary; self.location = location; self.problem = problem
    }
    init(_ update: CLLocationUpdate) {
        location = update.location
        if #available(iOS 18.0, *) {
            stationary = update.stationary
            if update.authorizationDenied || update.authorizationDeniedGlobally || update.authorizationRestricted { problem = .authorization }
            else if update.accuracyLimited { problem = .precision }
            else if update.serviceSessionRequired || update.insufficientlyInUse { problem = .backgroundAccess }
            else if update.locationUnavailable { problem = .unavailable }
        } else { stationary = update.isStationary }
    }
}

@MainActor
protocol MonitoringLocationService: AnyObject {
    var authorization: CLAuthorizationStatus { get }
    var precise: Bool { get }
    var isForeground: Bool { get }
    var authorizationChanged: (() -> Void)? { get set }
    var recoveredLocation: ((CLLocation) -> Void)? { get set }
    var recoveryFailed: ((CLError.Code?) -> Void)? { get set }
    func requestLegacyAuthorization()
    func beginSession()
    func endSession()
    func updates(_ configuration: CLLocationUpdate.LiveConfiguration) -> AsyncThrowingStream<MonitoringLocationUpdate, Error>
}

@MainActor
final class CoreLocationService: NSObject, MonitoringLocationService, CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    private var authorizationSession: (() -> Void)?
    private var backgroundSession: CLBackgroundActivitySession?
    private var requestedLegacyAlways = false
    var authorizationChanged: (() -> Void)?
    var recoveredLocation: ((CLLocation) -> Void)?
    var recoveryFailed: ((CLError.Code?) -> Void)?
    var authorization: CLAuthorizationStatus { manager.authorizationStatus }
    var precise: Bool { manager.accuracyAuthorization == .fullAccuracy }
    var isForeground: Bool { UIApplication.shared.applicationState == .active }

    override init() { super.init(); manager.delegate = self }

    func requestLegacyAuthorization() {
        guard isForeground else { return }
        if #unavailable(iOS 18.0) {
            switch authorization {
            case .notDetermined: manager.requestWhenInUseAuthorization()
            case .authorizedWhenInUse where !requestedLegacyAlways:
                requestedLegacyAlways = true; manager.requestAlwaysAuthorization()
            default: break
            }
        }
    }
    func beginSession() {
        authorizationSession?()
        if #available(iOS 18.0, *) {
            let session = CLServiceSession(authorization: .always)
            authorizationSession = { session.invalidate() }
        }
        if backgroundSession == nil { backgroundSession = CLBackgroundActivitySession() }
        if CLLocationManager.significantLocationChangeMonitoringAvailable() {
            manager.startMonitoringSignificantLocationChanges()
        }
    }
    func endSession() {
        manager.stopMonitoringSignificantLocationChanges()
        authorizationSession?(); authorizationSession = nil
        backgroundSession?.invalidate(); backgroundSession = nil
    }
    func updates(_ configuration: CLLocationUpdate.LiveConfiguration) -> AsyncThrowingStream<MonitoringLocationUpdate, Error> {
        AsyncThrowingStream { continuation in
            let producer = Task {
                do {
                    for try await update in CLLocationUpdate.liveUpdates(configuration) {
                        guard !Task.isCancelled else { break }
                        continuation.yield(MonitoringLocationUpdate(update))
                    }
                    continuation.finish()
                } catch { continuation.finish(throwing: error) }
            }
            continuation.onTermination = { _ in producer.cancel() }
        }
    }
    nonisolated func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        Task { @MainActor [weak self] in self?.authorizationChanged?() }
    }
    nonisolated func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last else { return }
        Task { @MainActor [weak self] in self?.recoveredLocation?(location) }
    }
    nonisolated func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        let code = (error as? CLError)?.code
        Task { @MainActor [weak self] in self?.recoveryFailed?(code) }
    }
}
