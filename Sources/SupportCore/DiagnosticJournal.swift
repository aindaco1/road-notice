import Foundation
import DustWaveSupport

// Only validated, location-free projections enter this file. Disk work runs on
// this actor; a full or unwritable journal never interrupts camera warnings.
public actor DiagnosticJournal {
    public struct Entry: Codable, Sendable { public var at: Date; public var event: SupportEvent; public var count: Int }
    private struct State: Codable { var events: [Entry] = []; var crashes: [CrashEvidence] = []; var drafts: [SupportReport] = [] }
    private let directory: URL
    private var state: State?
    public init(directory: URL) { self.directory = directory }
    private func load(now: Date) {
        if state == nil {
            if let data = try? Data(contentsOf: directory.appendingPathComponent("journal.json")), data.count <= 1_500_000,
               let saved = try? JSONDecoder().decode(State.self, from: data) { state = saved }
            else { state = State() }
        }
        state!.events = Array(state!.events.filter { now.timeIntervalSince($0.at) < 86_400 && ReportContract.validateEvent($0.event) }.suffix(500))
        state!.crashes = Array(state!.crashes.filter { c in
            guard let date = ISO8601DateFormatter().date(from: c.periodEnd) else { return false }
            return now.timeIntervalSince(date) < 7 * 86_400
        }.suffix(5))
        state!.drafts = Array(state!.drafts.filter { r in
            guard let date = ISO8601DateFormatter().date(from: r.createdAt), (try? r.encoded()) != nil else { return false }
            return now.timeIntervalSince(date) < 7 * 86_400
        }.suffix(5))
    }
    private func save() {
        do {
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
            var url = directory; var values = URLResourceValues(); values.isExcludedFromBackup = true
            try url.setResourceValues(values)
            while state!.events.count > 1, (try JSONEncoder().encode(state!.events)).count > 262_144 { state!.events.removeFirst() }
            let data = try JSONEncoder().encode(state!)
            guard data.count <= 1_500_000 else { return }
            #if os(iOS)
            try data.write(to: directory.appendingPathComponent("journal.json"), options: [.atomic, .completeFileProtectionUntilFirstUserAuthentication])
            #else
            try data.write(to: directory.appendingPathComponent("journal.json"), options: .atomic)
            #endif
        } catch { /* Best effort. Do not save raw filesystem errors in diagnostics. */ }
    }
    public func append(_ event: SupportEvent, now: Date = .now) {
        guard ReportContract.validateEvent(event) else { return }
        load(now: now)
        if let last = state!.events.last, last.event == event, now.timeIntervalSince(last.at) < 30 {
            state!.events[state!.events.count - 1].count = min(last.count + 1, 999)
        } else { state!.events.append(Entry(at: now, event: event, count: 1)) }
        load(now: now); save()
    }
    public func addCrash(_ crash: CrashEvidence, now: Date = .now) {
        let test = SupportReport(category: .crash, notes: "", crash: crash)
        guard (try? test.encoded()) != nil else { return }
        load(now: now)
        if !state!.crashes.contains(crash) { state!.crashes.append(crash) }
        load(now: now); save()
    }
    public func contents(now: Date = .now) -> (events: [SupportEvent], crashes: [CrashEvidence], drafts: [SupportReport]) {
        load(now: now); save()
        return (state!.events.suffix(40).map { entry in
            var values = entry.event.values
            let age = now.timeIntervalSince(entry.at)
            values["eventAge"] = age < 300 ? "justNow" : age < 3600 ? "lastHour" : "today"
            values["count"] = entry.count == 1 ? "one" : entry.count < 10 ? "few" : "many"
            return SupportEvent(entry.event.code, values)
        }, state!.crashes, state!.drafts)
    }
    public func saveDraft(_ report: SupportReport, now: Date = .now) throws {
        _ = try report.encoded(); load(now: now)
        if let old = state!.drafts.first(where: { $0.id == report.id }), old != report { throw ReportError.invalid }
        state!.drafts.removeAll { $0.id == report.id }; state!.drafts.append(report)
        load(now: now); save()
    }
    public func discard(_ id: String) { load(now: .now); state!.drafts.removeAll { $0.id == id }; save() }
    public func clear() { state = State(); save() }
}

public enum CrashFilter {
    // Apple's tree is untrusted input. Keep only app-relative offsets, never
    // raw addresses, system image paths, exception text or the original JSON.
    public static func frames(from data: Data) -> [CrashEvidence.Frame] {
        MetricKitStackProjection.frames(from: data, binaryNames: ["FineMeNot"])
            .map { .init(uuid: $0.uuid, offset: $0.offset) }
    }
}
