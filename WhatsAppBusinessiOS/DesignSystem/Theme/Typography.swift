//
//  Typography.swift
//  WhatsAppBusinessiOS
//
//  Typography system using SF Pro
//

import SwiftUI

extension Font {
    // MARK: - Headings

    static let largeTitle = Font.system(size: 34, weight: .bold, design: .rounded)
    static let title1 = Font.system(size: 28, weight: .bold, design: .rounded)
    static let title2 = Font.system(size: 22, weight: .bold, design: .rounded)
    static let title3 = Font.system(size: 20, weight: .semibold, design: .rounded)

    // MARK: - Headlines

    static let headline = Font.system(size: 17, weight: .semibold, design: .default)
    static let headlineRounded = Font.system(size: 17, weight: .semibold, design: .rounded)
    static let subheadline = Font.system(size: 15, weight: .medium, design: .default)

    // MARK: - Body

    static let bodyLarge = Font.system(size: 17, weight: .regular, design: .default)
    static let body = Font.system(size: 15, weight: .regular, design: .default)
    static let bodySmall = Font.system(size: 13, weight: .regular, design: .default)
    static let bodyBold = Font.system(size: 15, weight: .semibold, design: .default)

    // MARK: - Captions

    static let caption1 = Font.system(size: 12, weight: .regular, design: .default)
    static let caption2 = Font.system(size: 11, weight: .regular, design: .default)
    static let captionBold = Font.system(size: 12, weight: .semibold, design: .default)

    // MARK: - Footnote

    static let footnote = Font.system(size: 13, weight: .regular, design: .default)
    static let footnoteBold = Font.system(size: 13, weight: .semibold, design: .default)

    // MARK: - Custom Components

    static let messageBubble = Font.system(size: 16, weight: .regular, design: .default)
    static let timestamp = Font.system(size: 11, weight: .regular, design: .default)
    static let badge = Font.system(size: 12, weight: .semibold, design: .rounded)
    static let button = Font.system(size: 16, weight: .semibold, design: .default)
    static let buttonLarge = Font.system(size: 17, weight: .semibold, design: .default)
    static let input = Font.system(size: 16, weight: .regular, design: .default)
    static let navTitle = Font.system(size: 34, weight: .bold, design: .default)
    static let tabLabel = Font.system(size: 10, weight: .medium, design: .default)

    // MARK: - Numbers (Tabular)

    static let numberLarge = Font.system(size: 28, weight: .bold, design: .rounded).monospacedDigit()
    static let number = Font.system(size: 17, weight: .semibold, design: .rounded).monospacedDigit()
    static let numberSmall = Font.system(size: 13, weight: .medium, design: .rounded).monospacedDigit()

    // MARK: - Monospaced (for code/data)

    static let mono = Font.system(size: 14, weight: .regular, design: .monospaced)
    static let monoSmall = Font.system(size: 12, weight: .regular, design: .monospaced)
}

// MARK: - Text Styles (SwiftUI)

struct TextStyle {
    let font: Font
    let color: Color
    let lineSpacing: CGFloat?

    init(font: Font, color: Color = .textPrimary, lineSpacing: CGFloat? = nil) {
        self.font = font
        self.color = color
        self.lineSpacing = lineSpacing
    }
}

extension TextStyle {
    static let largeTitle = TextStyle(font: .largeTitle, color: .textPrimary)
    static let title1 = TextStyle(font: .title1, color: .textPrimary)
    static let title2 = TextStyle(font: .title2, color: .textPrimary)
    static let title3 = TextStyle(font: .title3, color: .textPrimary)

    static let headline = TextStyle(font: .headline, color: .textPrimary)
    static let subheadline = TextStyle(font: .subheadline, color: .textSecondary)

    static let body = TextStyle(font: .body, color: .textPrimary, lineSpacing: 2)
    static let bodySecondary = TextStyle(font: .body, color: .textSecondary, lineSpacing: 2)

    static let caption = TextStyle(font: .caption1, color: .textSecondary)
    static let footnote = TextStyle(font: .footnote, color: .textSecondary)
}

// MARK: - View Modifier for Text Styles

struct StyledText: ViewModifier {
    let style: TextStyle

    func body(content: Content) -> some View {
        content
            .font(style.font)
            .foregroundColor(style.color)
            .apply {
                if let lineSpacing = style.lineSpacing {
                    $0.lineSpacing(lineSpacing)
                } else {
                    $0
                }
            }
    }
}

extension View {
    func textStyle(_ style: TextStyle) -> some View {
        modifier(StyledText(style: style))
    }

    @ViewBuilder
    func apply<V: View>(@ViewBuilder _ transform: (Self) -> V) -> V {
        transform(self)
    }
}

// MARK: - UIFont Extensions (for UIKit components)

extension UIFont {
    static let sfProRounded = "SFProRounded"

    static func rounded(size: CGFloat, weight: Weight = .regular) -> UIFont {
        return UIFont.systemFont(ofSize: size, weight: weight)
            .rounded()
    }

    func rounded() -> UIFont {
        guard let descriptor = fontDescriptor.withDesign(.rounded) else {
            return self
        }
        return UIFont(descriptor: descriptor, size: pointSize)
    }

    static func monospacedDigit(size: CGFloat, weight: Weight = .regular) -> UIFont {
        return UIFont.monospacedSystemFont(ofSize: size, weight: weight)
    }
}

// MARK: - Dynamic Type Support

extension Font {
    static func scaledFont(size: CGFloat, weight: Font.Weight = .regular, design: Font.Design = .default) -> Font {
        return Font.system(size: size, weight: weight, design: design)
    }
}

// MARK: - Line Height Helpers

extension View {
    func lineHeight(_ lineHeight: CGFloat, font: Font) -> some View {
        self
            .font(font)
            .lineSpacing(lineHeight - (UIFont.systemFont(ofSize: 17).lineHeight))
    }
}
