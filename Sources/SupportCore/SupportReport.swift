import Foundation
import DustWaveSupport
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

public enum ReportCategory: String, Codable, CaseIterable, Sendable, Identifiable {
    case crash, missedWarning, unexpectedWarning, database, background, other
    public var id: String { rawValue }
    public var title: String {
        switch self {
        case .crash: "App crashed"
        case .missedWarning: "Missed warning"
        case .unexpectedWarning: "Unexpected warning"
        case .database: "Camera update failed"
        case .background: "Battery or background problem"
        case .other: "Something else"
        }
    }
}

public struct SupportEvent: Codable, Equatable, Sendable {
    public let code: String
    public let values: [String: String]
    public init(_ code: String, _ values: [String: String] = [:]) { self.code = code; self.values = values }
}

public struct CrashEvidence: Codable, Equatable, Sendable {
    public struct Frame: Codable, Equatable, Sendable {
        public let uuid: String
        public let offset: UInt64
        public init(uuid: String, offset: UInt64) { self.uuid = uuid; self.offset = offset }
    }
    public let kind: String
    public let version: String
    public let build: String
    public let periodEnd: String
    public let signal: Int
    public let exception: Int
    public let frames: [Frame]
    public init(kind: String, version: String, build: String, periodEnd: String, signal: Int, exception: Int, frames: [Frame]) {
        self.kind = kind; self.version = version; self.build = build; self.periodEnd = periodEnd
        self.signal = signal; self.exception = exception; self.frames = frames
    }
}

public struct SupportReport: Codable, Equatable, Sendable, Identifiable {
    public let schema: String
    public let id: String
    public let createdAt: String
    public let category: ReportCategory
    public let notes: String
    public let metadata: [String: String]
    public let state: [String: String]
    public let events: [SupportEvent]
    public let evidenceIndex: Int?
    public let crash: CrashEvidence?
    public init(category: ReportCategory, notes: String, metadata: [String: String] = [:],
                state: [String: String] = [:], events: [SupportEvent] = [], evidenceIndex: Int? = nil, crash: CrashEvidence? = nil,
                id: String = UUID().uuidString.lowercased(), now: Date = .now) {
        schema = "fine-me-not-issue-report-v1"; self.id = id
        createdAt = ISO8601DateFormatter().string(from: now)
        self.category = category; self.notes = notes; self.metadata = metadata
        self.state = state; self.events = events; self.evidenceIndex = evidenceIndex; self.crash = crash
    }
    public func encoded() throws -> Data {
        let encoder = JSONEncoder(); encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
        let data = try encoder.encode(self)
        try ReportContract.validate(data)
        return data
    }
    public var preview: String { (try? encoded()).flatMap { String(data: $0, encoding: .utf8) } ?? "Report is not valid." }
}

public enum ReportContract {
    public static let maximumBytes = 32_768
    public static let rules: [String: [String]] = {
        let url = Bundle.module.url(forResource: "report-contract", withExtension: "json")!
        return try! JSONDecoder().decode([String: [String]].self, from: Data(contentsOf: url))
    }()
    public static func matches(_ value: String, _ pattern: String) -> Bool {
        value.range(of: pattern, options: .regularExpression) != nil
    }
    public static func validateEvent(_ event: SupportEvent) -> Bool {
        rules["events"]!.contains(event.code) && event.values.allSatisfy { rules[$0.key]?.contains($0.value) == true && $0.key != "events" }
    }
    public static func validate(_ data: Data) throws {
        func require(_ valid: Bool) throws { if !valid { throw ReportError.invalid } }
        try require(data.count <= maximumBytes)
        let object = try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
        try require(Set(object.keys).isSubset(of: ["schema", "id", "createdAt", "category", "notes", "metadata", "state", "events", "evidenceIndex", "crash"]))
        let r = try JSONDecoder().decode(SupportReport.self, from: data)
        try require(r.schema == "fine-me-not-issue-report-v1" && UUID(uuidString: r.id) != nil && r.id == r.id.lowercased())
        try require(ISO8601DateFormatter().date(from: r.createdAt) != nil)
        try require(r.notes.unicodeScalars.count <= 2000 && r.notes.utf8.count <= 8192)
        try require(!r.notes.unicodeScalars.contains { CharacterSet.controlCharacters.contains($0) && $0 != "\n" && $0 != "\t" })
        try require(!r.notes.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || !r.state.isEmpty || r.crash != nil || !r.events.isEmpty)
        let patterns = ["version": "^[0-9]{1,3}(\\.[0-9]{1,3}){0,3}$", "build": "^[0-9]{1,8}$", "os": "^[0-9]{1,3}(\\.[0-9]{1,3}){0,3}$", "model": "^iPhone[0-9]{1,3},[0-9]{1,3}$", "database": "^[a-zA-Z0-9_-]{1,80}$", "records": "^[0-9]{1,6}$", "channel": "^(distribution|development)$"]
        try require(r.metadata.allSatisfy { key, value in patterns[key].map { matches(value, $0) } == true })
        try require(r.state.allSatisfy { rules[$0.key]?.contains($0.value) == true && $0.key != "events" })
        try require(r.events.count <= 40 && r.events.allSatisfy(validateEvent))
        if let index = r.evidenceIndex { try require(r.events.indices.contains(index)) }
        for e in object["events"] as? [[String: Any]] ?? [] { try require(Set(e.keys) == ["code", "values"]) }
        if let c = r.crash {
            try require(["crash", "hang"].contains(c.kind) && matches(c.version, patterns["version"]!) && matches(c.build, patterns["build"]!))
            try require(ISO8601DateFormatter().date(from: c.periodEnd) != nil && (0...128).contains(c.signal) && (0...128).contains(c.exception))
            try require(c.frames.count <= 32 && c.frames.allSatisfy { UUID(uuidString: $0.uuid) != nil && $0.uuid == $0.uuid.lowercased() && $0.offset <= 0xFFFFFFFF })
            let raw = object["crash"] as? [String: Any] ?? [:]
            try require(Set(raw.keys) == ["kind", "version", "build", "periodEnd", "signal", "exception", "frames"])
            for frame in raw["frames"] as? [[String: Any]] ?? [] { try require(Set(frame.keys) == ["uuid", "offset"]) }
        }
    }
}

public enum ReportError: Error, LocalizedError {
    case invalid, rejected, unavailable, invalidReceipt
    public var errorDescription: String? {
        switch self {
        case .invalid: "This report needs a shorter description or valid technical details."
        case .rejected: "The report wasn’t accepted. Your draft is still here. Try again later."
        case .unavailable: "Couldn’t reach the reporting service. Your draft is still here. Retry when connected."
        case .invalidReceipt: "Delivery isn’t confirmed yet. Retry this same draft to check without posting it twice."
        }
    }
}

public struct ReportReceipt: Codable, Sendable {
    public let ok: Bool
    public let reportId: String
    public let action: String
    public let issueNumber: Int
    public var url: URL { URL(string: "https://github.com/aindaco1/road-notice/issues/\(issueNumber)")! }
}

public enum ReportClient {
    public static func send(_ report: SupportReport) async throws -> ReportReceipt {
        let config = URLSessionConfiguration.ephemeral
        config.timeoutIntervalForRequest = 25; config.timeoutIntervalForResource = 35
        return try await send(report, configuration: config)
    }
    static func send(_ report: SupportReport, configuration config: URLSessionConfiguration) async throws -> ReportReceipt {
        let payload = try report.encoded()
        var request = URLRequest(url: URL(string: "https://crash.dustwave.xyz/v1/fine-me-not/reports")!)
        request.httpMethod = "POST"; request.httpBody = payload
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("FineMeNot-Reports/1", forHTTPHeaderField: "User-Agent")
        do {
            let endpoint = request.url
            let (data, _) = try await BoundedReportTransport().send(request, maximumResponseBytes: 4096, configuration: config) { response in
                guard response.statusCode == 200, response.url == endpoint else { throw ReportError.rejected }
            }
            // Retain the consumer's decoding-error precedence and public receipt type.
            let receipt = try JSONDecoder().decode(ReportReceipt.self, from: data)
            do {
                _ = try ReportAcknowledgement.decode(data, reportID: report.id, maximumBytes: 4096, maximumIssueNumber: Int.max)
            } catch { throw ReportError.invalidReceipt }
            return receipt
        } catch let error as ReportError { throw error }
        catch ReportTransportError.responseTooLarge { throw ReportError.invalidReceipt }
        catch { throw ReportError.unavailable }
    }
}
