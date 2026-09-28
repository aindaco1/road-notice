import Foundation
import Observation
import AVFAudio
import UserNotifications
import CameraCore
import UIKit

@MainActor
protocol MonitoringWarningPresenter: AnyObject {
    func present(_ warnings: [CameraWarning])
    func requestNotifications() async
}

@MainActor @Observable
final class AlertPresenter: NSObject, AVAudioPlayerDelegate, MonitoringWarningPresenter {
    private(set) var isPlaying = false
    private(set) var audioError: String?
    private(set) var route = "Current audio output"
    private(set) var volume: Float = 0
    private(set) var lastWarning: String?
    private(set) var notificationStatus = "Not checked"
    private(set) var lastAudioEvent = UserDefaults.standard.string(forKey: "warnings.lastAudioEvent") ?? "No audio attempt recorded"
    private(set) var supportAudio = "none"
    private(set) var supportNotifications = "unknown"
    private(set) var supportSound = "unknown"
    var supportState: [String: String] {
        let ports = audio.currentRoute.outputs.map(\.portType)
        let kind = ports.contains(.carAudio) ? "carPlay" : ports.contains(where: { [.bluetoothA2DP, .bluetoothHFP, .bluetoothLE].contains($0) }) ? "bluetooth" : ports.contains(.builtInSpeaker) ? "speaker" : ports.contains(.headphones) ? "wired" : "other"
        return ["route": kind, "volume": volume == 0 ? "muted" : volume < 0.15 ? "low" : "audible", "audio": supportAudio, "notifications": supportNotifications, "notificationSound": supportSound]
    }
    private func supportResult(_ code: String) {
        supportAudio = code
        var values = supportState
        values["appState"] = SupportDiagnostics.appState
        values["lowPower"] = ProcessInfo.processInfo.isLowPowerModeEnabled ? "yes" : "no"
        SupportDiagnostics.shared.record("audio", values)
    }
    private var attemptContext = ""
    private var player: AVAudioPlayer?
    private var notificationObservers: [NSObjectProtocol] = []
    private let audio = AVAudioSession.sharedInstance()

    override init() {
        super.init()
        for name in [AVAudioSession.routeChangeNotification, AVAudioSession.interruptionNotification,
                     AVAudioSession.mediaServicesWereResetNotification] {
            notificationObservers.append(NotificationCenter.default.addObserver(forName: name, object: nil, queue: .main) { [weak self] notification in
                let name = notification.name
                let interrupted = (notification.userInfo?[AVAudioSessionInterruptionTypeKey] as? UInt)
                    == AVAudioSession.InterruptionType.began.rawValue
                Task { @MainActor [weak self] in
                    guard let self else { return }
                    if interrupted || name == AVAudioSession.mediaServicesWereResetNotification {
                        if self.isPlaying {
                            self.audioError = "Warning audio was interrupted."
                            self.recordAudioResult("Interrupted")
                            self.supportResult("interrupted")
                        }
                        self.finish()
                    }
                    self.refreshRoute()
                }
            })
        }
        refreshRoute()
    }

    func refreshRoute() {
        route = audio.currentRoute.outputs.map(\.portName).joined(separator: ", ")
        if route.isEmpty { route = "System-selected output" }
        volume = audio.outputVolume
    }

    func requestNotifications() async {
        _ = try? await UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound])
        await refreshNotificationStatus()
    }

    func refreshNotificationStatus() async {
        let settings = await UNUserNotificationCenter.current().notificationSettings()
        let allowed = settings.authorizationStatus == .authorized || settings.authorizationStatus == .provisional
        supportNotifications = allowed ? "allowed" : "denied"
        supportSound = settings.soundSetting == .enabled ? "yes" : "no"
        notificationStatus = "\(allowed ? "Allowed" : "Not allowed") · sound \(settings.soundSetting == .enabled ? "on" : "off") · time sensitive \(settings.timeSensitiveSetting == .enabled ? "on" : "off")"
    }

    private func recordAudioResult(_ result: String) {
        lastAudioEvent = "\(attemptContext)\n\(result)"
        // Only the latest audio attempt survives a relaunch. No coordinates or trip log.
        UserDefaults.standard.set(lastAudioEvent, forKey: "warnings.lastAudioEvent")
    }

    func present(_ warnings: [CameraWarning]) {
        guard let first = warnings.first else { return }
        let title = warnings.count == 1 ? first.camera.kind.title : "Cameras nearby"
        let body = warnings.map { "\($0.camera.kind.title): \($0.camera.label)" }.joined(separator: "\n")
        lastWarning = "\(title) · \(first.camera.label)"
        let didStart = playSiren(context: lastWarning ?? title)
        let content = UNMutableNotificationContent()
        content.title = title; content.body = body
        content.interruptionLevel = .timeSensitive
        // Direct audio is the Silent-mode path. A soundless notification avoids
        // sounding twice; ordinary sound is only a degraded fallback.
        content.sound = didStart ? nil : .default
        let request = UNNotificationRequest(identifier: UUID().uuidString, content: content, trigger: nil)
        Task {
            do { try await UNUserNotificationCenter.current().add(request) }
            catch { notificationStatus = "Could not post notification: \(error.localizedDescription)" }
        }
    }

    @discardableResult
    func playSiren(context: String = "Parked sound test") -> Bool {
        guard !isPlaying else { return true }
        audioError = nil
        refreshRoute()
        let state = UIApplication.shared.applicationState == .active ? "foreground" : "background / locked"
        attemptContext = "\(Date.now.formatted(date: .abbreviated, time: .standard)) · \(context)\n\(state) · Low Power Mode \(ProcessInfo.processInfo.isLowPowerModeEnabled ? "on" : "off")"
        var stage = "sessionFailed"
        do {
            try audio.setCategory(.playback, mode: .default, options: [.duckOthers])
            try audio.setActive(true)
            stage = "fileMissing"
            guard let url = Bundle.main.url(forResource: "siren", withExtension: "wav") else {
                throw CocoaError(.fileNoSuchFile)
            }
            stage = "decodeFailed"
            let player = try AVAudioPlayer(contentsOf: url)
            player.delegate = self; player.numberOfLoops = 0; player.volume = 1
            self.player = player
            stage = "playFailed"
            guard player.play() else { throw CocoaError(.fileReadUnknown) }
            isPlaying = true; refreshRoute()
            attemptContext += "\n\(route) · media volume \(Int(volume * 100))%"
            recordAudioResult("Playback started")
            supportResult("started")
            return true
        } catch {
            supportResult(stage)
            audioError = "Couldn't play the siren. \(error.localizedDescription)"
            recordAudioResult(audioError ?? "Playback failed")
            finish(); return false
        }
    }

    private func finish() {
        player?.stop(); player = nil; isPlaying = false
        try? audio.setActive(false, options: .notifyOthersOnDeactivation)
    }

    nonisolated func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        let identifier = ObjectIdentifier(player)
        Task { @MainActor [weak self] in
            guard let self, let current = self.player, ObjectIdentifier(current) == identifier else { return }
            if !flag { self.audioError = "Warning audio did not finish." }
            self.supportResult(flag ? "completed" : "finishFailed")
            self.recordAudioResult(flag ? "Playback completed" : "Playback did not finish")
            self.finish()
        }
    }
    nonisolated func audioPlayerDecodeErrorDidOccur(_ player: AVAudioPlayer, error: Error?) {
        let identifier = ObjectIdentifier(player)
        Task { @MainActor [weak self] in
            guard let self, let current = self.player, ObjectIdentifier(current) == identifier else { return }
            self.audioError = "Couldn't decode the warning sound."
            self.supportResult("decodeFailed")
            self.recordAudioResult("Sound decode failed"); self.finish()
        }
    }
}
