import Foundation
import Testing
@testable import SupportCore

private final class ReportStub: URLProtocol, @unchecked Sendable {
    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func startLoading() {
        let stream = request.httpBodyStream!
        stream.open()
        defer { stream.close() }
        var input = Data()
        var buffer = [UInt8](repeating: 0, count: 1024)
        while stream.hasBytesAvailable {
            let count = stream.read(&buffer, maxLength: buffer.count)
            if count <= 0 { break }
            input.append(contentsOf: buffer.prefix(count))
        }
        let report = try! JSONDecoder().decode(SupportReport.self, from: input)
        let scenario = report.notes
        var receipt: [String: Any] = ["ok": true, "reportId": report.id, "action": "created", "issueNumber": 7]
        if scenario == "wrong-id" { receipt["reportId"] = UUID().uuidString }
        if scenario == "upper-id" { receipt["reportId"] = report.id.uppercased() }
        if scenario == "pending" { receipt["action"] = "pending" }
        if scenario == "duplicate" { receipt["action"] = "duplicate" }
        if scenario == "zero-issue" { receipt["issueNumber"] = 0 }
        if scenario == "false-ok" { receipt["ok"] = false }
        if scenario == "network" {
            client?.urlProtocol(self, didFailWithError: URLError(.timedOut))
            return
        }
        let response = HTTPURLResponse(url: request.url!, statusCode: scenario == "status" ? 429 : 200,
                                       httpVersion: nil, headerFields: nil)!
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        let body = scenario == "oversized" || scenario == "status" ? Data(repeating: 32, count: 4097)
            : scenario == "malformed" ? Data("not json".utf8) : try! JSONSerialization.data(withJSONObject: receipt)
        client?.urlProtocol(self, didLoad: body)
        client?.urlProtocolDidFinishLoading(self)
    }
    override func stopLoading() {}
}

@Test func reviewedTransportRetainsReceiptAndFailureSemantics() async throws {
    for scenario in ["created", "duplicate", "wrong-id", "upper-id", "pending", "zero-issue", "false-ok", "oversized", "status", "malformed", "network"] {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [ReportStub.self]
        let report = SupportReport(category: .other, notes: scenario)
        do {
            let receipt = try await ReportClient.send(report, configuration: configuration)
            #expect(["created", "duplicate"].contains(scenario))
            #expect(receipt.reportId == report.id)
            #expect(receipt.issueNumber == 7)
        } catch let error as ReportError {
            switch error {
            case .rejected: #expect(scenario == "status")
            case .unavailable: #expect(["malformed", "network"].contains(scenario))
            case .invalidReceipt: #expect(["wrong-id", "upper-id", "pending", "zero-issue", "false-ok", "oversized"].contains(scenario))
            case .invalid: Issue.record("valid synthetic report rejected")
            }
        }
    }
}
