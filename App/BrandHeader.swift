import SwiftUI

/// The same icon and two-line wordmark used at finemenot.xyz.
struct BrandHeader: View {
    @ScaledMetric(relativeTo: .largeTitle) private var typeSize = 48
    @ScaledMetric(relativeTo: .largeTitle) private var iconSize = 100

    var body: some View {
        ViewThatFits(in: .horizontal) {
            HStack(alignment: .center, spacing: 18) {
                icon
                wordmark.fixedSize()
            }
            VStack(alignment: .leading, spacing: 18) {
                icon
                wordmark
            }
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Fine Me Not")
        .accessibilityAddTraits(.isHeader)
    }

    private var icon: some View {
        Image("BrandIcon")
            .resizable()
            .scaledToFit()
            .frame(width: min(iconSize, 168), height: min(iconSize, 168))
            .clipShape(RoundedRectangle(cornerRadius: min(iconSize, 168) * 0.22))
    }

    private var wordmark: some View {
        VStack(alignment: .leading, spacing: -typeSize * 0.15) {
            Text("FINE")
            Text("ME NOT")
        }
        .font(.system(size: typeSize, weight: .bold, design: .monospaced))
        .tracking(-typeSize * 0.08)
        .foregroundStyle(.white)
        .lineLimit(1)
        .minimumScaleFactor(0.5)
    }
}

#Preview {
    BrandHeader()
        .padding(24)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(red: 10 / 255, green: 0, blue: 148 / 255))
}
