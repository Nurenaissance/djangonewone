//
//  PrimaryButton.swift
//  WhatsAppBusinessiOS
//
//  Primary button component with loading state
//

import SwiftUI

struct PrimaryButton: View {
    let title: String
    let action: () -> Void
    var isLoading: Bool = false
    var isDisabled: Bool = false
    var icon: String? = nil
    var style: ButtonStyle = .filled

    var body: some View {
        Button(action: action) {
            HStack(spacing: Spacing.iconText) {
                if let icon = icon, !isLoading {
                    Image(systemName: icon)
                        .font(.button)
                }

                if isLoading {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: textColor))
                } else {
                    Text(title)
                        .font(.button)
                }
            }
            .frame(maxWidth: .infinity)
            .frame(height: Layout.buttonHeight)
            .background(backgroundColor)
            .foregroundColor(textColor)
            .cornerRadius(CornerRadius.button)
            .overlay(
                RoundedRectangle(cornerRadius: CornerRadius.button)
                    .stroke(borderColor, lineWidth: style == .outlined ? 2 : 0)
            )
            .opacity(isDisabled || isLoading ? 0.6 : 1.0)
        }
        .disabled(isDisabled || isLoading)
    }

    // MARK: - Computed Properties

    private var backgroundColor: Color {
        switch style {
        case .filled:
            return isDisabled ? Color(.systemGray3) : Color.primary
        case .outlined:
            return Color.clear
        case .text:
            return Color.clear
        }
    }

    private var textColor: Color {
        switch style {
        case .filled:
            return .white
        case .outlined, .text:
            return .primary
        }
    }

    private var borderColor: Color {
        return isDisabled ? Color(.systemGray3) : Color.primary
    }

    // MARK: - Button Style Enum

    enum ButtonStyle {
        case filled
        case outlined
        case text
    }
}

// MARK: - Secondary Button

struct SecondaryButton: View {
    let title: String
    let action: () -> Void
    var isLoading: Bool = false
    var isDisabled: Bool = false
    var icon: String? = nil

    var body: some View {
        PrimaryButton(
            title: title,
            action: action,
            isLoading: isLoading,
            isDisabled: isDisabled,
            icon: icon,
            style: .outlined
        )
    }
}

// MARK: - Icon Button

struct IconButton: View {
    let icon: String
    let action: () -> Void
    var size: CGFloat = Layout.iconButtonSize
    var foregroundColor: Color = .primary

    var body: some View {
        Button(action: action) {
            Image(systemName: icon)
                .font(.title3)
                .foregroundColor(foregroundColor)
                .frame(width: size, height: size)
                .background(Color.clear)
                .cornerRadius(CornerRadius.sm)
        }
    }
}

// MARK: - Floating Action Button

struct FloatingActionButton: View {
    let icon: String
    let action: () -> Void
    var backgroundColor: Color = .primary
    var size: CGFloat = 56

    var body: some View {
        Button(action: action) {
            Image(systemName: icon)
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundColor(.white)
                .frame(width: size, height: size)
                .background(backgroundColor)
                .cornerRadius(size / 2)
                .elevation(Elevation.large)
        }
    }
}

// MARK: - Preview

#Preview("Primary Buttons") {
    VStack(spacing: 20) {
        PrimaryButton(
            title: "Sign In",
            action: {},
            icon: "arrow.right"
        )

        PrimaryButton(
            title: "Loading...",
            action: {},
            isLoading: true
        )

        PrimaryButton(
            title: "Disabled",
            action: {},
            isDisabled: true
        )

        SecondaryButton(
            title: "Cancel",
            action: {}
        )

        PrimaryButton(
            title: "Text Button",
            action: {},
            style: .text
        )

        HStack {
            IconButton(icon: "magnifyingglass", action: {})
            IconButton(icon: "ellipsis", action: {})
            IconButton(icon: "trash", action: {}, foregroundColor: .error)
        }

        FloatingActionButton(icon: "plus", action: {})
    }
    .padding()
}
