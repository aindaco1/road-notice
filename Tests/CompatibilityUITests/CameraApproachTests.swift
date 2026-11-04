import XCTest
import CoreLocation

final class CameraApproachTests: XCTestCase {
    private struct Route: Decodable {
        let latitude, startLongitude, endLongitude, speedMetersPerSecond, courseDegrees: Double
    }

    @MainActor
    private func setSwitch(_ toggle: XCUIElement, value: String, allow: XCUIElement? = nil) {
        // Hosted simulators can ignore the first input after launch. Retry only
        // when the requested state was not applied, never blindly toggle twice.
        for _ in 0..<2 {
            if toggle.value as? String != value { toggle.tap() }
            if let allow, allow.waitForExistence(timeout: 3) { allow.tap() }
            let settled = XCTNSPredicateExpectation(predicate: NSPredicate(format: "value == %@", value), object: toggle)
            if XCTWaiter.wait(for: [settled], timeout: 10) == .completed { return }
        }
        XCTFail("Switch must reach its requested state before the next action")
    }

    @MainActor
    private func launchApp() -> XCUIApplication {
        continueAfterFailure = false
        let app = XCUIApplication()
        app.launchArguments = ["-warnings.enabled", "NO", "-warnings.encounters", ""]
        app.launch()
        let springboard = XCUIApplication(bundleIdentifier: "com.apple.springboard")
        for _ in 0..<4 {
            let allowLocation = springboard.buttons["Allow While Using App"]
            let allowNotifications = springboard.buttons["Allow"]
            if allowLocation.exists { allowLocation.tap() }
            else if allowNotifications.exists { allowNotifications.tap() }
            else { break }
        }
        let warnings = app.switches["Camera warnings"]
        XCTAssertTrue(warnings.waitForExistence(timeout: 60))
        // Exercise real opt-in once, then confirm monitoring before driving.
        setSwitch(warnings, value: "1", allow: springboard.buttons["Allow"])
        return app
    }

    @MainActor
    func testForegroundSirenAndSettings() {
        let app = launchApp()
        let quiet = app.switches["speed-check-toggle"]
        XCTAssertEqual(quiet.value as? String, "1")
        setSwitch(quiet, value: "0")
        app.terminate()
        app.launch()
        XCTAssertTrue(quiet.waitForExistence(timeout: 60))
        XCTAssertEqual(quiet.value as? String, "0")
        setSwitch(quiet, value: "1")
        let warning = app.buttons["test-warning"]
        if !warning.isHittable { app.swipeUp() }
        warning.tap()
        Thread.sleep(forTimeInterval: 3)
        XCTAssertEqual(app.state, .runningForeground)
        // The outer runner independently requires foreground audio completion.
    }

    @MainActor
    func testBackgroundCameraApproach() throws {
        continueAfterFailure = false
        let device = XCUIDevice.shared
        let url = try XCTUnwrap(Bundle(for: CameraApproachTests.self).url(forResource: "camera-approach", withExtension: "json"))
        let route = try JSONDecoder().decode(Route.self, from: Data(contentsOf: url))
        let latitude = route.latitude
        let startLongitude = route.startLongitude
        let endLongitude = route.endLongitude
        func setLocation(_ longitude: Double) {
            device.location = XCUILocation(location: CLLocation(
                coordinate: CLLocationCoordinate2D(latitude: latitude, longitude: longitude),
                altitude: 0, horizontalAccuracy: 5, verticalAccuracy: 5,
                course: route.courseDegrees, courseAccuracy: 1, speed: route.speedMetersPerSecond, speedAccuracy: 0.5,
                timestamp: Date()))
        }
        defer { device.location = nil }
        setLocation(startLongitude)
        let app = launchApp()
        device.press(.home)
        XCTAssertTrue(app.wait(for: .runningBackground, timeout: 15))
        let duration = (endLongitude - startLongitude) * .pi / 180 * 6_371_000 * cos(latitude * .pi / 180) / route.speedMetersPerSecond
        let started = ProcessInfo.processInfo.systemUptime
        while true {
            let fraction = min((ProcessInfo.processInfo.systemUptime - started) / duration, 1)
            setLocation(startLongitude + (endLongitude - startLongitude) * fraction)
            if fraction == 1 { break }
            Thread.sleep(forTimeInterval: 2)
        }
        Thread.sleep(forTimeInterval: 10)
        // The outer runner asserts exactly one completed background siren from
        // the app's persisted journal, independently of this route driver.
    }

    @MainActor
    func testCameraNotificationPersistsInAlertLog() throws {
        try testBackgroundCameraApproach()
        let app = XCUIApplication()
        app.terminate()
        app.launch()
        XCTAssertTrue(app.switches["Camera warnings"].waitForExistence(timeout: 60))
        let log = app.buttons["alert-log"]
        for _ in 0..<4 where !log.isHittable { app.swipeUp() }
        log.tap()
        XCTAssertTrue(app.navigationBars["Alert log"].waitForExistence(timeout: 10))
        let item = app.buttons.matching(NSPredicate(format: "label CONTAINS %@", "Gibson between Carlisle and San Mateo")).firstMatch
        XCTAssertTrue(item.waitForExistence(timeout: 10))
        item.tap()
        XCTAssertTrue(app.navigationBars["Camera alert"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.staticTexts["Gibson between Carlisle and San Mateo · EB"].exists)
        let screenshot = XCTAttachment(screenshot: app.screenshot())
        screenshot.name = "Saved camera alert details"
        screenshot.lifetime = .keepAlways
        add(screenshot)
    }

    @MainActor
    func testColdNotificationDefaultAction() throws {
        try testBackgroundCameraApproach()
        let app = XCUIApplication()
        app.terminate()
        let springboard = XCUIApplication(bundleIdentifier: "com.apple.springboard")
        XCUIDevice.shared.press(.home)
        springboard.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.01))
            .press(forDuration: 0.1, thenDragTo: springboard.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.8)))
        // Scroll the notification content; an edge swipe dismisses the shade.
        springboard.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.745))
            .press(forDuration: 0.1, thenDragTo: springboard.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.255)))
        let matches = springboard.buttons.matching(NSPredicate(format: "label CONTAINS %@", "Speed camera: Gibson between Carlisle and San Mateo"))
        let item = try XCTUnwrap(matches.allElementsBoundByIndex.first(where: { $0.isHittable }))
        item.tap()
        if !app.navigationBars["Camera alert"].waitForExistence(timeout: 3), item.exists {
            // Some simulator Notification Center versions need swipe-to-open.
            item.swipeRight()
            let open = springboard.buttons["Open"]
            if open.waitForExistence(timeout: 3) { open.tap() }
        }
        XCTAssertTrue(app.navigationBars["Camera alert"].waitForExistence(timeout: 15))
        XCTAssertTrue(app.staticTexts["Gibson between Carlisle and San Mateo · EB"].exists)
        let screenshot = XCTAttachment(screenshot: app.screenshot())
        screenshot.name = "Opened notification after termination"
        screenshot.lifetime = .keepAlways
        add(screenshot)
    }
}
