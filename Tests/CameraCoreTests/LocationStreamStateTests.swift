import Foundation
import Testing
@testable import CameraCore

private let streamStart = Date(timeIntervalSince1970: 1_790_500_000)

@Test func stationaryOvernightKeepsTheSameNavigationStream() throws {
    var state = LocationStreamState()
    let sessionValue = state.begin()
    let session = try #require(sessionValue)
    state.receive(stationary: true, at: streamStart, session: session)
    #expect(state.isTracking)
    #expect(state.stationary)
    // Re-entering the foreground or a recovery callback must not start another
    // provider or terminate the one that is waiting for automatic resume.
    let duplicate = state.begin()
    #expect(duplicate == nil)
    let morning = streamStart.addingTimeInterval(8 * 3600)
    state.receive(stationary: false, at: morning, session: session)
    #expect(state.isCurrent(session))
    #expect(!state.stationary)
    #expect(state.resumedAt == morning)
}

@Test func poorFirstResumedFixDoesNotKeepLocationInStationaryState() throws {
    var state = LocationStreamState()
    let sessionValue = state.begin()
    let session = try #require(sessionValue)
    state.receive(stationary: true, at: streamStart, session: session)
    let departure = streamStart.addingTimeInterval(600)
    // No speed threshold or good GPS fix is needed to clear idle state.
    state.receive(stationary: false, at: departure, session: session)
    state.recordFix(accuracy: 300, usable: false, at: departure, session: session)
    #expect(!state.stationary)
    #expect(state.firstResumedAccuracy == 300)
    #expect(state.resumedUsableFixDelay == nil)
    state.recordFix(accuracy: 12, usable: true, at: departure.addingTimeInterval(3), session: session)
    #expect(state.firstResumedAccuracy == 300)
    #expect(state.resumedUsableFixDelay == 3)
    state.recordFix(accuracy: 5, usable: true, at: departure.addingTimeInterval(4), session: session)
    #expect(state.resumedUsableFixDelay == 3)
}

@Test func absentOrUnavailableFixDoesNotInventStationaryEvidence() throws {
    var state = LocationStreamState()
    let sessionValue = state.begin()
    let session = try #require(sessionValue)
    state.receive(stationary: false, at: streamStart, session: session)
    #expect(!state.stationary)
    #expect(state.resumedAt == nil)
    state.recordFix(accuracy: -1, usable: false, at: streamStart, session: session)
    #expect(!state.stationary)
    #expect(state.resumedUsableFixDelay == nil)
}

@Test func cancelledSessionCannotResumeOrStopAReplacement() throws {
    var state = LocationStreamState()
    let oldValue = state.begin()
    let old = try #require(oldValue)
    state.receive(stationary: true, at: streamStart, session: old)
    state.stop()
    #expect(!state.isTracking)
    #expect(!state.stationary)
    let newValue = state.begin()
    let new = try #require(newValue)
    state.receive(stationary: true, at: streamStart, session: old)
    state.recordFix(accuracy: 5, usable: true, at: streamStart, session: old)
    let endedOld = state.end(old)
    #expect(!endedOld)
    #expect(state.isCurrent(new))
    #expect(!state.stationary)
    #expect(state.resumedAt == nil)
}

@Test func failedStreamCanRestartAndThenPauseAndResume() throws {
    var state = LocationStreamState()
    let failedValue = state.begin()
    let failed = try #require(failedValue)
    let endedFailed = state.end(failed)
    #expect(endedFailed)
    #expect(!state.isTracking)
    let retryValue = state.begin()
    let retry = try #require(retryValue)
    #expect(retry != failed)
    state.receive(stationary: true, at: streamStart, session: retry)
    state.receive(stationary: false, at: streamStart.addingTimeInterval(120), session: retry)
    state.recordFix(accuracy: 8, usable: true, at: streamStart.addingTimeInterval(120), session: retry)
    #expect(state.isTracking)
    #expect(state.resumedUsableFixDelay == 0)
}

@Test func repeatedStationaryPeriodsMeasureEachResumeSeparately() throws {
    var state = LocationStreamState()
    let sessionValue = state.begin()
    let session = try #require(sessionValue)
    state.receive(stationary: true, at: streamStart, session: session)
    state.receive(stationary: false, at: streamStart.addingTimeInterval(120), session: session)
    state.recordFix(accuracy: 8, usable: true, at: streamStart.addingTimeInterval(120), session: session)
    state.receive(stationary: true, at: streamStart.addingTimeInterval(240), session: session)
    state.receive(stationary: false, at: streamStart.addingTimeInterval(360), session: session)
    #expect(state.firstResumedAccuracy == nil)
    #expect(state.resumedUsableFixDelay == nil)
    state.recordFix(accuracy: -1, usable: false, at: streamStart.addingTimeInterval(360), session: session)
    state.recordFix(accuracy: 20, usable: true, at: streamStart.addingTimeInterval(365), session: session)
    #expect(state.firstResumedAccuracy == nil)
    #expect(state.resumedUsableFixDelay == 5)
}
