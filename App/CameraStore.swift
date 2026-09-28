import Foundation
import Observation
import CryptoKit
import CameraCore

@MainActor
protocol MonitoringCameraStore: AnyObject {
    var snapshot: CameraSnapshot? { get }
    var index: CameraIndex { get }
    var isDue: Bool { get }
    func refresh(force: Bool) async -> Bool
}

@MainActor @Observable
final class CameraStore: MonitoringCameraStore {
    private(set) var snapshot: CameraSnapshot?
    private(set) var index = CameraIndex(cameras: [])
    private(set) var isUpdating = false
    private(set) var lastCheck: Date?
    private(set) var updateError: String?
    private(set) var supportStage = "idle"
    private(set) var supportResult = "none"
    private let defaults: UserDefaults
    private let directory: URL
    private let session: URLSession
    private let baseURL: URL
    private var lastAttempt: Date?

    init(defaults: UserDefaults = .standard, baseURL: URL = AppLinks.database,
         supportDirectory: URL = .applicationSupportDirectory) {
        self.defaults = defaults
        self.baseURL = baseURL
        // A newer saved public snapshot must not replace a private candidate's
        // reviewed inputs. Keep the public cache path for normal upgrades.
        let channel = SHA256.hash(data: Data(baseURL.absoluteString.utf8)).map { String(format: "%02x", $0) }.joined()
        let cache = baseURL == AppLinks.publicDatabase ? "FineMeNot" : "FineMeNot-\(channel.prefix(12))"
        directory = supportDirectory.appending(path: cache, directoryHint: .isDirectory)
        let config = URLSessionConfiguration.ephemeral
        config.timeoutIntervalForRequest = 20
        config.timeoutIntervalForResource = 45
        session = URLSession(configuration: config)
        lastCheck = defaults.object(forKey: "database.lastCheck") as? Date
        do { try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true) }
        catch { updateError = "Couldn't prepare the offline database." }
        let urls = [directory.appending(path: "cameras.json"), directory.appending(path: "previous.json"),
                    Bundle.main.url(forResource: "cameras", withExtension: "json")].compactMap { $0 }
        for url in urls {
            if let data = try? Data(contentsOf: url), let value = try? CameraSnapshot.decode(data),
               (try? value.validate()) != nil,
               snapshot == nil || value.generatedAt > snapshot!.generatedAt {
                // An app update can ship an urgent correction newer than the
                // downloaded copy. Always choose the newest valid offline data.
                installInMemory(value)
            }
        }
        if snapshot == nil { updateError = "No usable camera database. Try Update now." }
    }

    var isDue: Bool { snapshot.map { UpdateSchedule.isDue(generatedAt: $0.generatedAt, now: .now) } ?? true }

    @discardableResult
    func refresh(force: Bool = false) async -> Bool {
        guard !isUpdating else { return false }
        if !force {
            guard isDue, lastAttempt.map({ Date.now.timeIntervalSince($0) > 3600 }) ?? true else { return true }
        }
        isUpdating = true; updateError = nil; lastAttempt = .now
        defer { isUpdating = false }
        supportStage = "manifest"; supportResult = "started"
        defer { SupportDiagnostics.shared.record("database", ["databaseStage": supportStage, "databaseResult": supportResult]) }
        do {
            let manifestData = try await fetch(baseURL.appending(path: "manifest.json"), maximumBytes: 100_000)
            let decoder = JSONDecoder(); decoder.dateDecodingStrategy = .iso8601
            let manifest = try decoder.decode(Manifest.self, from: manifestData)
            guard manifest.schemaVersion == 1, manifest.recordCount > 0, manifest.recordCount <= 100_000,
                  manifest.file.range(of: #"^[A-Za-z0-9_-]+\.json$"#, options: .regularExpression) != nil,
                  manifest.sha256.count == 64 else { throw DatabaseError.invalidManifest }
            if manifest.version != snapshot?.version {
                supportStage = "download"
                let data = try await fetch(baseURL.appending(path: manifest.file), maximumBytes: 20_000_000)
                supportStage = "validation"
                let digest = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
                guard digest == manifest.sha256 else { throw DatabaseError.checksum }
                let incoming = try CameraSnapshot.decode(data)
                try incoming.validate()
                guard incoming.version == manifest.version, incoming.cameras.count == manifest.recordCount,
                      incoming.generatedAt == manifest.generatedAt else { throw DatabaseError.invalidManifest }
                if let snapshot, incoming.generatedAt < snapshot.generatedAt { throw DatabaseError.rollback }
                try Task.checkCancellation()
                supportStage = "save"
                let installed = directory.appending(path: "cameras.json")
                if let previous = try? Data(contentsOf: installed) {
                    try previous.write(to: directory.appending(path: "previous.json"), options: [.atomic, .completeFileProtectionUntilFirstUserAuthentication])
                }
                try data.write(to: installed, options: [.atomic, .completeFileProtectionUntilFirstUserAuthentication])
                installInMemory(incoming)
            }
            supportStage = "complete"; supportResult = "ok"
            lastCheck = .now; defaults.set(lastCheck, forKey: "database.lastCheck")
            return true
        } catch {
            supportResult = error is CancellationError ? "cancelled" : error is URLError ? "network" : supportStage == "save" ? "storage" : "invalid"
            if !(error is CancellationError) { updateError = "Update failed. Using saved cameras. \(error.localizedDescription)" }
            return false
        }
    }

    private func installInMemory(_ value: CameraSnapshot) {
        snapshot = value; index = CameraIndex(cameras: value.cameras)
    }

    private func fetch(_ url: URL, maximumBytes: Int) async throws -> Data {
        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.setValue("FineMeNot/0.1", forHTTPHeaderField: "User-Agent")
        let (bytes, response) = try await session.bytes(for: request)
        guard let response = response as? HTTPURLResponse, response.statusCode == 200,
              response.url?.scheme == "https", response.url?.host == baseURL.host,
              response.expectedContentLength <= maximumBytes else { throw DatabaseError.invalidManifest }
        var data = Data()
        for try await byte in bytes {
            guard data.count < maximumBytes else { throw DatabaseError.invalidSnapshot }
            data.append(byte)
        }
        return data
    }
    private struct Manifest: Decodable {
        let schemaVersion: Int
        let version: String
        let generatedAt: Date
        let file: String
        let sha256: String
        let recordCount: Int
    }
}
