// CI-only control app: isolates simulator GPS delivery from Road Notice.
import UIKit
import CoreLocation

@main
final class LocationProbe: UIResponder, UIApplicationDelegate, CLLocationManagerDelegate {
    var window: UIWindow?
    private let manager = CLLocationManager()
    private var fixes: [[String: Any]] = []

    func application(_ application: UIApplication, didFinishLaunchingWithOptions options: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        let window = UIWindow(frame: UIScreen.main.bounds)
        window.rootViewController = UIViewController()
        window.makeKeyAndVisible()
        self.window = window
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBestForNavigation
        let filter = UserDefaults.standard.string(forKey: "distanceFilter") ?? "10"
        manager.distanceFilter = filter == "none" ? kCLDistanceFilterNone : Double(filter)!
        manager.activityType = .automotiveNavigation
        manager.allowsBackgroundLocationUpdates = true
        manager.pausesLocationUpdatesAutomatically = false
        return true
    }

    func applicationDidBecomeActive(_ application: UIApplication) {
        manager.startUpdatingLocation()
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        for location in locations {
            fixes.append(["distanceFilter": manager.distanceFilter,
                          "latitude": location.coordinate.latitude,
                          "longitude": location.coordinate.longitude,
                          "timestamp": location.timestamp.timeIntervalSince1970,
                          "state": UIApplication.shared.applicationState.rawValue])
        }
        let url = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent("fixes.json")
        if let data = try? JSONSerialization.data(withJSONObject: fixes, options: .prettyPrinted) {
            try? data.write(to: url, options: .atomic)
        }
    }
}
