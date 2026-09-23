import SwiftUI
import BackgroundTasks
import UserNotifications
import CameraCore

@MainActor
final class AppServices {
    static let shared = AppServices()
    static let refreshID = "xyz.dustwave.fine-me-not.database-refresh"
    let store: CameraStore
    let presenter: AlertPresenter
    let monitoring: MonitoringController
    private init() {
        SupportDiagnostics.shared.start()
        store = CameraStore()
        presenter = AlertPresenter()
        monitoring = MonitoringController(store: store, presenter: presenter)
    }

    func diagnosticReport(at now: Date) -> String {
        let info = Bundle.main.infoDictionary ?? [:]
        let build = "\(info["CFBundleShortVersionString"] as? String ?? "?") (\(info["CFBundleVersion"] as? String ?? "?"))"
        let match = monitoring.matchDiagnostic
        func age(_ date: Date?) -> String {
            date.map { "\(max(0, Int(now.timeIntervalSince($0)))) seconds ago" } ?? "none"
        }
        func number(_ value: Double?, unit: String) -> String {
            value.map { String(format: "%.1f %@", $0, unit) } ?? "unavailable"
        }
        let postedLimit = match.speedLimit.map { "\($0.value) \($0.unit) · \($0.sourceID) · expires \($0.validUntil.formatted())" } ?? "unknown"
        let refresh: String
        switch UIApplication.shared.backgroundRefreshStatus {
        case .available: refresh = "available"
        case .denied: refresh = "off"
        case .restricted: refresh = "restricted"
        @unknown default: refresh = "unknown"
        }
        return """
        Road Notice \(build) · iOS \(UIDevice.current.systemVersion)
        Database: \(store.snapshot?.version ?? "unavailable")
        Status: \(monitoring.status(at: now))
        Always location: \(monitoring.authorization == .authorizedAlways ? "yes" : "no") · precise: \(monitoring.precise ? "yes" : "no")
        Continuous GPS: \(monitoring.isTracking ? "requested" : "off") · automatic pauses: disabled
        Low Power Mode: \(ProcessInfo.processInfo.isLowPowerModeEnabled ? "on" : "off") · Background App Refresh: \(refresh)
        Latest GPS: \(age(monitoring.lastReceivedAt)) · accepted GPS: \(age(monitoring.lastFixAt))
        Accuracy: \(number(monitoring.lastAccuracy, unit: "m")) · reported speed: \(number(monitoring.lastReportedSpeed, unit: "m/s"))
        GPS result: \(monitoring.fixStatus)
        Effective speed: \(number(match.speed, unit: "m/s")) · course: \(number(match.course, unit: "degrees"))
        Nearest mapped camera: \(match.cameraLabel ?? "none within 1 km") · \(number(match.distance, unit: "m"))
        Match result: \(match.reason.rawValue)
        Speed uncertainty: \(number(monitoring.lastSpeedAccuracy, unit: "m/s"))
        Camera limit: \(postedLimit)
        Quiet below speed limit: \(monitoring.quietBelowSpeedLimit ? "on" : "off")
        Notifications: \(presenter.notificationStatus)
        Current audio: \(presenter.route) · media volume \(Int(presenter.volume * 100))%
        Latest audio attempt:
        \(presenter.lastAudioEvent)
        """
    }

    func scheduleRefresh() {
        let request = BGAppRefreshTaskRequest(identifier: Self.refreshID)
        request.earliestBeginDate = store.isDue ? Date.now.addingTimeInterval(900) : UpdateSchedule.nextRefresh(after: .now)
        try? BGTaskScheduler.shared.submit(request)
    }

    func handleRefresh(_ task: BGTask) {
        let operation = Task { @MainActor in
            let success = await store.refresh(force: true)
            task.setTaskCompleted(success: success)
            scheduleRefresh()
        }
        task.expirationHandler = { operation.cancel() }
    }
}

@MainActor
final class AppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate {
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {
        let services = AppServices.shared
        UNUserNotificationCenter.current().delegate = self
        BGTaskScheduler.shared.register(forTaskWithIdentifier: AppServices.refreshID, using: .main) { task in
            MainActor.assumeIsolated { AppServices.shared.handleRefresh(task) }
        }
        services.monitoring.start()
        services.scheduleRefresh()
        return true
    }

    nonisolated func userNotificationCenter(_ center: UNUserNotificationCenter,
                                            willPresent notification: UNNotification) async -> UNNotificationPresentationOptions {
        [.banner, .sound]
    }
}

@main
struct FineMeNotApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) private var delegate
    @Environment(\.scenePhase) private var scenePhase
    private let services = AppServices.shared
    var body: some Scene {
        WindowGroup {
            SettingsView(services: services)
                .preferredColorScheme(.dark)
                .task {
                    await services.presenter.refreshNotificationStatus()
                    await services.store.refresh()
                }
                .onChange(of: scenePhase) { _, phase in
                    SupportDiagnostics.shared.record("lifecycle", ["appState": SupportDiagnostics.appState, "lowPower": ProcessInfo.processInfo.isLowPowerModeEnabled ? "yes" : "no"])
                    if phase == .active {
                        services.monitoring.refreshAuthorization()
                        services.monitoring.start()
                        services.presenter.refreshRoute()
                        Task {
                            await services.presenter.refreshNotificationStatus()
                            await services.store.refresh()
                        }
                    } else if phase == .background { services.scheduleRefresh() }
                }
        }
    }
}
