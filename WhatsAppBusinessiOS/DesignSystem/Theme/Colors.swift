//
//  Colors.swift
//  WhatsAppBusinessiOS
//
//  Design system colors with dark mode support
//

import SwiftUI

extension Color {
    // MARK: - Brand Colors (Emerald Theme)

    static let emerald50 = Color(hex: "ECFDF5")
    static let emerald100 = Color(hex: "D1FAE5")
    static let emerald200 = Color(hex: "A7F3D0")
    static let emerald300 = Color(hex: "6EE7B7")
    static let emerald400 = Color(hex: "34D399")
    static let emerald500 = Color(hex: "10B981")  // Primary
    static let emerald600 = Color(hex: "059669")  // Primary Dark
    static let emerald700 = Color(hex: "047857")  // Accent
    static let emerald800 = Color(hex: "065F46")
    static let emerald900 = Color(hex: "064E3B")

    // MARK: - Semantic Colors

    static let primary = emerald500
    static let primaryDark = emerald600
    static let primaryLight = emerald400
    static let accent = emerald700

    static let success = Color(hex: "22C55E")
    static let warning = Color(hex: "F59E0B")
    static let error = Color(hex: "EF4444")
    static let info = Color(hex: "3B82F6")

    // MARK: - Message Bubbles

    static let sentBubble = emerald500
    static let receivedBubble = Color(.systemGray6)
    static let sentBubbleText = Color.white
    static let receivedBubbleText = Color(.label)

    // MARK: - Text Colors (Dark Mode Adaptive)

    static let textPrimary = Color(.label)
    static let textSecondary = Color(.secondaryLabel)
    static let textTertiary = Color(.tertiaryLabel)
    static let textQuaternary = Color(.quaternaryLabel)

    // MARK: - Background Colors (Dark Mode Adaptive)

    static let backgroundPrimary = Color(.systemBackground)
    static let backgroundSecondary = Color(.secondarySystemBackground)
    static let backgroundTertiary = Color(.tertiarySystemBackground)
    static let backgroundGrouped = Color(.systemGroupedBackground)

    // MARK: - UI Element Colors

    static let separator = Color(.separator)
    static let link = Color(.link)
    static let placeholderText = Color(.placeholderText)

    // MARK: - Badge Colors

    static let unreadBadge = emerald500
    static let notificationBadge = error

    // MARK: - Status Colors

    static let statusOnline = success
    static let statusOffline = Color(.systemGray)
    static let statusAway = warning

    // MARK: - Chart Colors

    static let chartPrimary = emerald500
    static let chartSecondary = Color(hex: "8B5CF6")  // Purple
    static let chartTertiary = info
    static let chartQuaternary = warning
    static let chartQuinary = error

    // MARK: - Gradient Colors

    static let gradientStart = emerald400
    static let gradientEnd = emerald600

    static var primaryGradient: LinearGradient {
        LinearGradient(
            colors: [gradientStart, gradientEnd],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
    }

    // MARK: - Tag Colors

    static let tagBlue = Color(hex: "3B82F6")
    static let tagPurple = Color(hex: "8B5CF6")
    static let tagPink = Color(hex: "EC4899")
    static let tagOrange = warning
    static let tagYellow = Color(hex: "EAB308")
    static let tagGreen = success
    static let tagTeal = Color(hex: "14B8A6")
    static let tagIndigo = Color(hex: "6366F1")

    static let tagColors: [Color] = [
        tagBlue, tagPurple, tagPink, tagOrange,
        tagYellow, tagGreen, tagTeal, tagIndigo
    ]

    // MARK: - Helper for Hex Colors

    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)

        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }

        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }

    // MARK: - Color for Status

    static func colorForCampaignStatus(_ status: CampaignStatus) -> Color {
        switch status {
        case .draft: return Color(.systemGray)
        case .scheduled: return info
        case .sending: return warning
        case .completed: return success
        case .failed: return error
        case .cancelled: return Color(.systemGray2)
        }
    }

    static func colorForMessageStatus(_ status: MessageStatus) -> Color {
        switch status {
        case .pending: return Color(.systemGray)
        case .sent: return Color(.systemGray)
        case .delivered: return emerald500
        case .read: return emerald600
        case .failed: return error
        }
    }
}

// MARK: - UIColor Extensions (for UIKit components)

extension UIColor {
    static let emerald500 = UIColor(red: 16/255, green: 185/255, blue: 129/255, alpha: 1.0)
    static let emerald600 = UIColor(red: 5/255, green: 150/255, blue: 105/255, alpha: 1.0)

    convenience init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)

        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }

        self.init(
            red: CGFloat(r) / 255,
            green: CGFloat(g) / 255,
            blue: CGFloat(b) / 255,
            alpha: CGFloat(a) / 255
        )
    }
}
