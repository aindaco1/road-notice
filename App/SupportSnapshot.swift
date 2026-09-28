import Foundation
import UIKit
import CoreLocation
import CameraCore
import SupportCore

extension MatchReason {
    var supportCode: String {
        switch self {
        case .invalidFix: "invalidFix"
        case .outOfOrder: "outOfOrder"
        case .notMoving: "notMoving"
        case .noCamera: "noCamera"
        case .tooFar: "tooFar"
        case .oppositeDirection: "oppositeDirection"
        case .behind: "behind"
        case .approachUnconfirmed, .outsideRoad, .ambiguousRoad: "approachUnconfirmed"
        case .cooldown: "cooldown"
        case .expired: "expired"
        case .belowSpeedLimit: "belowSpeedLimit"
        case .warning: "warning"
        }
    }
}

extension MonitoringController {
    var supportState: [String: String] {
        let location: String
        switch authorization {
        case .authorizedAlways: location = "always"
        case .authorizedWhenInUse: location = "whenInUse"
        case .denied: location = "denied"
        case .restricted: location = "restricted"
        default: location = "unknown"
        }
        let age = lastFixAt.map { Date.now.timeIntervalSince($0) }
        return ["location": location, "precise": precise ? "yes" : "no",
                "monitoring": isTracking ? "requested" : "off", "quiet": quietBelowSpeedLimit ? "yes" : "no",
                "match": matchDiagnostic.reason.supportCode,
                "fixAge": age.map { $0 <= 15 ? "fresh" : $0 < 300 ? "recent" : "old" } ?? "none",
                "accuracy": lastAccuracy.map { $0 < 0 ? "unknown" : $0 <= 25 ? "good" : $0 <= 75 ? "usable" : "poor" } ?? "unknown"]
    }
}

extension AppServices {
    var supportMetadata: [String: String] {
        let info = Bundle.main.infoDictionary ?? [:]
        var result = ["version": info["CFBundleShortVersionString"] as? String ?? "0", "build": info["CFBundleVersion"] as? String ?? "0",
                      "os": UIDevice.current.systemVersion, "channel": "distribution"]
        #if DEBUG
        result["channel"] = "development"
        #endif
        result["model"] = SupportDiagnostics.model
        result["database"] = store.snapshot?.version
        result["records"] = store.snapshot.map { String($0.cameras.count) }
        return result
    }
    var supportState: [String: String] {
        var state = monitoring.supportState
        state.merge(presenter.supportState) { _, new in new }
        state["appState"] = SupportDiagnostics.appState
        state["lowPower"] = ProcessInfo.processInfo.isLowPowerModeEnabled ? "yes" : "no"
        switch UIApplication.shared.backgroundRefreshStatus {
        case .available: state["refresh"] = "available"
        case .denied: state["refresh"] = "denied"
        case .restricted: state["refresh"] = "restricted"
        @unknown default: state["refresh"] = "unknown"
        }
        state["databaseAge"] = store.snapshot == nil ? "unknown" : store.isDue ? "old" : "current"
        state["databaseStage"] = store.supportStage
        state["databaseResult"] = store.supportResult
        return state
    }
}
