//
//  Spacing.swift
//  WhatsAppBusinessiOS
//
//  8-point grid spacing system
//

import SwiftUI

enum Spacing {
    // MARK: - Base Spacing (8pt grid)

    static let xxs: CGFloat = 4
    static let xs: CGFloat = 8
    static let sm: CGFloat = 12
    static let md: CGFloat = 16
    static let lg: CGFloat = 24
    static let xl: CGFloat = 32
    static let xxl: CGFloat = 48
    static let xxxl: CGFloat = 64

    // MARK: - Component-Specific Spacing

    static let messageBubblePadding: CGFloat = 12
    static let cardPadding: CGFloat = 16
    static let screenPadding: CGFloat = 16
    static let listRowPadding: CGFloat = 12
    static let sectionPadding: CGFloat = 24
    static let bottomSheetPadding: CGFloat = 20

    // MARK: - Vertical Spacing

    static let verticalTight: CGFloat = 4
    static let verticalCompact: CGFloat = 8
    static let verticalComfortable: CGFloat = 12
    static let verticalRelaxed: CGFloat = 16
    static let verticalSpacious: CGFloat = 24

    // MARK: - Horizontal Spacing

    static let horizontalTight: CGFloat = 4
    static let horizontalCompact: CGFloat = 8
    static let horizontalComfortable: CGFloat = 12
    static let horizontalRelaxed: CGFloat = 16
    static let horizontalSpacious: CGFloat = 24

    // MARK: - Icon Spacing

    static let iconText: CGFloat = 8  // Space between icon and text
    static let iconSmall: CGFloat = 16
    static let iconMedium: CGFloat = 24
    static let iconLarge: CGFloat = 32
    static let iconXLarge: CGFloat = 48

    // MARK: - Safe Area Insets

    static let safeAreaTopOffset: CGFloat = 8
    static let safeAreaBottomOffset: CGFloat = 8
}

enum CornerRadius {
    // MARK: - Base Corner Radius

    static let xxs: CGFloat = 4
    static let xs: CGFloat = 6
    static let sm: CGFloat = 8
    static let md: CGFloat = 12
    static let lg: CGFloat = 16
    static let xl: CGFloat = 20
    static let xxl: CGFloat = 24
    static let pill: CGFloat = 999  // Fully rounded

    // MARK: - Component-Specific Radius

    static let messageBubble: CGFloat = 16
    static let card: CGFloat = 12
    static let button: CGFloat = 12
    static let buttonSmall: CGFloat = 8
    static let buttonLarge: CGFloat = 16
    static let tag: CGFloat = 8
    static let input: CGFloat = 10
    static let sheet: CGFloat = 20
    static let avatar: CGFloat = 999  // Fully rounded
}

enum Elevation {
    // MARK: - Shadow Styles

    static let none = ElevationStyle(
        color: .clear,
        radius: 0,
        x: 0,
        y: 0
    )

    static let small = ElevationStyle(
        color: Color.black.opacity(0.05),
        radius: 2,
        x: 0,
        y: 1
    )

    static let medium = ElevationStyle(
        color: Color.black.opacity(0.1),
        radius: 4,
        x: 0,
        y: 2
    )

    static let large = ElevationStyle(
        color: Color.black.opacity(0.15),
        radius: 8,
        x: 0,
        y: 4
    )

    static let xlarge = ElevationStyle(
        color: Color.black.opacity(0.2),
        radius: 16,
        x: 0,
        y: 8
    )
}

struct ElevationStyle {
    let color: Color
    let radius: CGFloat
    let x: CGFloat
    let y: CGFloat
}

// MARK: - View Extensions for Spacing

extension View {
    /// Apply standard screen padding
    func screenPadding() -> some View {
        self.padding(Spacing.screenPadding)
    }

    /// Apply standard card padding
    func cardPadding() -> some View {
        self.padding(Spacing.cardPadding)
    }

    /// Apply custom elevation/shadow
    func elevation(_ style: ElevationStyle) -> some View {
        self.shadow(
            color: style.color,
            radius: style.radius,
            x: style.x,
            y: style.y
        )
    }

    /// Apply standard card style (rounded corners + shadow)
    func cardStyle() -> some View {
        self
            .background(Color.backgroundSecondary)
            .cornerRadius(CornerRadius.card)
            .elevation(Elevation.small)
    }

    /// Apply message bubble style
    func messageBubbleStyle(isSent: Bool) -> some View {
        self
            .padding(Spacing.messageBubblePadding)
            .background(isSent ? Color.sentBubble : Color.receivedBubble)
            .foregroundColor(isSent ? Color.sentBubbleText : Color.receivedBubbleText)
            .cornerRadius(CornerRadius.messageBubble)
    }
}

// MARK: - Edge Insets Helpers

extension EdgeInsets {
    static let screenPadding = EdgeInsets(
        top: Spacing.screenPadding,
        leading: Spacing.screenPadding,
        bottom: Spacing.screenPadding,
        trailing: Spacing.screenPadding
    )

    static let cardPadding = EdgeInsets(
        top: Spacing.cardPadding,
        leading: Spacing.cardPadding,
        bottom: Spacing.cardPadding,
        trailing: Spacing.cardPadding
    )

    static let listRowPadding = EdgeInsets(
        top: Spacing.listRowPadding,
        leading: Spacing.listRowPadding,
        bottom: Spacing.listRowPadding,
        trailing: Spacing.listRowPadding
    )

    static func horizontal(_ value: CGFloat) -> EdgeInsets {
        EdgeInsets(top: 0, leading: value, bottom: 0, trailing: value)
    }

    static func vertical(_ value: CGFloat) -> EdgeInsets {
        EdgeInsets(top: value, leading: 0, bottom: value, trailing: 0)
    }
}

// MARK: - Layout Constants

enum Layout {
    // MARK: - Standard Sizes

    static let avatarSmall: CGFloat = 32
    static let avatarMedium: CGFloat = 40
    static let avatarLarge: CGFloat = 56
    static let avatarXLarge: CGFloat = 80

    static let buttonHeight: CGFloat = 50
    static let buttonHeightSmall: CGFloat = 36
    static let buttonHeightLarge: CGFloat = 56

    static let inputHeight: CGFloat = 44
    static let inputHeightSmall: CGFloat = 36
    static let inputHeightLarge: CGFloat = 52

    static let iconButtonSize: CGFloat = 44  // Apple HIG minimum tap target

    static let listRowHeight: CGFloat = 60
    static let contactCardWidth: CGFloat = 160
    static let contactCardHeight: CGFloat = 200

    static let navBarHeight: CGFloat = 44
    static let tabBarHeight: CGFloat = 49  // iOS standard

    static let sheetHandleWidth: CGFloat = 40
    static let sheetHandleHeight: CGFloat = 5

    // MARK: - Animation Durations

    static let animationFast: Double = 0.2
    static let animationNormal: Double = 0.3
    static let animationSlow: Double = 0.5

    // MARK: - Haptic Feedback Settings

    static let hapticEnabled = true
}

// MARK: - Grid System

enum Grid {
    static let columns2: [GridItem] = Array(repeating: GridItem(.flexible(), spacing: Spacing.md), count: 2)
    static let columns3: [GridItem] = Array(repeating: GridItem(.flexible(), spacing: Spacing.md), count: 3)
    static let columns4: [GridItem] = Array(repeating: GridItem(.flexible(), spacing: Spacing.md), count: 4)

    static let adaptiveSmall: [GridItem] = [GridItem(.adaptive(minimum: 100, maximum: 150), spacing: Spacing.md)]
    static let adaptiveMedium: [GridItem] = [GridItem(.adaptive(minimum: 150, maximum: 200), spacing: Spacing.md)]
    static let adaptiveLarge: [GridItem] = [GridItem(.adaptive(minimum: 200, maximum: 300), spacing: Spacing.md)]

    static let contactGrid: [GridItem] = [GridItem(.adaptive(minimum: Layout.contactCardWidth), spacing: Spacing.md)]
}
