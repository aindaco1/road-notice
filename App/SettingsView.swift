import SwiftUI
import CameraCore

struct SettingsView: View {
    let services: AppServices
    @State private var showingReport = false
    private let blue = Color(red: 10 / 255, green: 0, blue: 148 / 255)
    private let accent = Color(red: 174 / 255, green: 207 / 255, blue: 1)
    @Environment(\.openURL) private var openURL

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 32) {
                VStack(alignment: .leading, spacing: 12) {
                    BrandHeader()
                    Text("Speed cameras ahead.\nKeep your cash.")
                        .font(.system(.body, design: .monospaced)).foregroundStyle(accent)
                }
                VStack(spacing: 0) {
                    row {
                        Toggle("Camera warnings", isOn: Binding(get: { services.monitoring.enabled }, set: { services.monitoring.setEnabled($0) }))
                            .font(.system(.headline, design: .monospaced)).tint(accent)
                            .accessibilityIdentifier("warnings-toggle")
                    }
                    row {
                        VStack(alignment: .leading, spacing: 10) {
                            Toggle("Quiet below speed limit", isOn: Binding(
                                get: { services.monitoring.quietBelowSpeedLimit },
                                set: { services.monitoring.setQuietBelowSpeedLimit($0) }))
                                .font(.system(.headline, design: .monospaced)).tint(accent)
                                .accessibilityIdentifier("speed-check-toggle")
                            Text("Speed cameras only. If your speed or the camera's limit is unknown, you'll still get a warning. Red-light warnings stay on.")
                                .font(.footnote).foregroundStyle(accent)
                        }
                    }
                    row {
                        VStack(alignment: .leading, spacing: 8) {
                            caption("STATUS")
                            TimelineView(.periodic(from: .now, by: 5)) { context in
                                Text(services.monitoring.status(at: context.date))
                                    .font(.system(.body, design: .monospaced))
                            }
                            if services.monitoring.enabled && (services.monitoring.authorization != .authorizedAlways || !services.monitoring.precise) {
                                Button("Open location settings") {
                                    openURL(URL(string: UIApplication.openSettingsURLString)!)
                                }.foregroundStyle(accent)
                                Text("Choose Always and turn on Precise Location. Background warnings use more battery.")
                                    .font(.footnote).foregroundStyle(accent)
                            }
                        }.frame(maxWidth: .infinity, alignment: .leading)
                    }
                    row {
                        VStack(alignment: .leading, spacing: 10) {
                            Button { services.presenter.playSiren() } label: {
                                HStack {
                                    Text(services.presenter.isPlaying ? "Siren playing" : "Test warning")
                                    Spacer()
                                    Image(systemName: "speaker.wave.3.fill")
                                }.font(.system(.headline, design: .monospaced)).contentShape(Rectangle())
                            }.disabled(services.presenter.isPlaying).accessibilityIdentifier("test-warning")
                            Text("Loud 2-second siren. Test while parked.").font(.footnote).foregroundStyle(accent)
                            Text(services.presenter.route).font(.footnote).foregroundStyle(accent)
                            if services.presenter.volume < 0.15 {
                                Text("Media volume is low. Turn it up to hear warnings.").font(.footnote)
                            }
                            if let error = services.presenter.audioError { Text(error).font(.footnote) }
                        }
                    }
                    row {
                        VStack(alignment: .leading, spacing: 10) {
                            caption("CAMERA DATABASE")
                            if let snapshot = services.store.snapshot {
                                Text("\(snapshot.cameras.count.formatted()) warning locations")
                                    .font(.system(.body, design: .monospaced))
                                Text("Published \(snapshot.generatedAt.formatted(date: .abbreviated, time: .omitted))")
                                    .font(.footnote).foregroundStyle(accent)
                                Text(snapshot.coverage).font(.footnote).foregroundStyle(accent)
                            } else { Text("No camera database available").font(.footnote) }
                            if let checked = services.store.lastCheck {
                                Text("Last checked \(checked.formatted(date: .abbreviated, time: .shortened))")
                                    .font(.footnote).foregroundStyle(accent)
                            }
                            if let error = services.store.updateError { Text(error).font(.footnote) }
                            Button(services.store.isUpdating ? "Updating…" : "Update now") {
                                Task { await services.store.refresh(force: true) }
                            }.disabled(services.store.isUpdating).foregroundStyle(accent)
                                .accessibilityIdentifier("update-database")
                            Text("Weekly updates: Sunday night at midnight Mountain Time. Downloads catch up when your phone can connect.")
                                .font(.footnote).foregroundStyle(accent)
                        }.frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
                Button("Report a problem") { showingReport = true }
                    .font(.system(.headline, design: .monospaced)).foregroundStyle(accent)
                    .accessibilityIdentifier("report-problem")
                DisclosureGroup("Diagnostics") {
                    VStack(alignment: .leading, spacing: 12) {
                        TimelineView(.periodic(from: .now, by: 5)) { context in
                            Text(services.diagnosticReport(at: context.date))
                                .font(.system(.caption, design: .monospaced)).textSelection(.enabled)
                        }
                        Button("Copy local diagnostics") {
                            UIPasteboard.general.string = services.diagnosticReport(at: .now)
                        }.foregroundStyle(accent).accessibilityIdentifier("copy-diagnostics")
                        Text("These local details can include camera names, times, speeds and audio names. Review before sharing. Report a problem uses a separate, location-free summary.")
                            .font(.caption).foregroundStyle(accent)
                    }.frame(maxWidth: .infinity, alignment: .leading).padding(.top, 12)
                }.font(.system(.footnote, design: .monospaced)).tint(accent)
                VStack(alignment: .leading, spacing: 14) {
                    Text("Free. Open source.\nNo ads. No subscriptions.")
                        .font(.system(.footnote, design: .monospaced))
                    Link("Sources, privacy & support ↗", destination: AppLinks.website)
                        .foregroundStyle(accent).font(.footnote)
                    Text("Camera data © OpenStreetMap contributors · ODbL")
                        .font(.caption).foregroundStyle(accent)
                    Text("Camera coverage is incomplete. Location permissions, phone state, and audio volume affect warnings. Always follow posted signs.")
                        .font(.caption).foregroundStyle(accent)
                }
            }.padding(24).frame(maxWidth: 560, alignment: .leading).frame(maxWidth: .infinity)
        }.background(blue.ignoresSafeArea()).foregroundStyle(.white)
        .sheet(isPresented: $showingReport) { ReportProblemView(services: services) }
    }

    private func caption(_ text: String) -> some View {
        Text(text).font(.system(.caption, design: .monospaced, weight: .semibold)).tracking(1).foregroundStyle(accent)
    }
    private func row<Content: View>(@ViewBuilder _ content: () -> Content) -> some View {
        VStack(spacing: 0) {
            Rectangle().fill(accent.opacity(0.4)).frame(height: 1)
            content().padding(.vertical, 20)
        }
    }
}
