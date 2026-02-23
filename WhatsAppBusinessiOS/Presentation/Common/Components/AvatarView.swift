//
//  AvatarView.swift
//  WhatsAppBusinessiOS
//
//  Avatar component with initials fallback
//

import SwiftUI

struct AvatarView: View {
    let name: String
    let imageURL: String?
    var size: CGFloat = Layout.avatarMedium
    var backgroundColor: Color?

    var body: some View {
        Group {
            if let urlString = imageURL, let url = URL(string: urlString) {
                AsyncImage(url: url) { phase in
                    switch phase {
                    case .empty:
                        InitialsAvatar(name: name, size: size, backgroundColor: backgroundColor)
                    case .success(let image):
                        image
                            .resizable()
                            .aspectRatio(contentMode: .fill)
                    case .failure:
                        InitialsAvatar(name: name, size: size, backgroundColor: backgroundColor)
                    @unknown default:
                        InitialsAvatar(name: name, size: size, backgroundColor: backgroundColor)
                    }
                }
            } else {
                InitialsAvatar(name: name, size: size, backgroundColor: backgroundColor)
            }
        }
        .frame(width: size, height: size)
        .clipShape(Circle())
    }
}

// MARK: - Initials Avatar

struct InitialsAvatar: View {
    let name: String
    let size: CGFloat
    let backgroundColor: Color?

    var body: some View {
        ZStack {
            Circle()
                .fill(backgroundColor ?? colorForName(name))

            Text(initials)
                .font(fontSize)
                .fontWeight(.semibold)
                .foregroundColor(.white)
        }
    }

    // MARK: - Computed Properties

    private var initials: String {
        let components = name.split(separator: " ")
        if components.count >= 2 {
            return String(components[0].prefix(1) + components[1].prefix(1)).uppercased()
        } else {
            return String(name.prefix(2)).uppercased()
        }
    }

    private var fontSize: Font {
        switch size {
        case 0..<40:
            return .caption1
        case 40..<60:
            return .headline
        default:
            return .title2
        }
    }

    private func colorForName(_ name: String) -> Color {
        let colors: [Color] = [
            .tagBlue, .tagPurple, .tagPink, .tagOrange,
            .tagGreen, .tagTeal, .tagIndigo
        ]

        let hash = name.hashValue
        let index = abs(hash) % colors.count
        return colors[index]
    }
}

// MARK: - Avatar with Status

struct AvatarWithStatus: View {
    let name: String
    let imageURL: String?
    var size: CGFloat = Layout.avatarMedium
    var isOnline: Bool = false

    var body: some View {
        ZStack(alignment: .bottomTrailing) {
            AvatarView(name: name, imageURL: imageURL, size: size)

            if isOnline {
                Circle()
                    .fill(Color.statusOnline)
                    .frame(width: size * 0.25, height: size * 0.25)
                    .overlay(
                        Circle()
                            .stroke(Color.backgroundPrimary, lineWidth: 2)
                    )
            }
        }
    }
}

// MARK: - Avatar Group (Stacked Avatars)

struct AvatarGroup: View {
    let names: [String]
    let imageURLs: [String?]
    var size: CGFloat = Layout.avatarSmall
    var maxVisible: Int = 3

    var body: some View {
        HStack(spacing: -size * 0.3) {
            ForEach(0..<min(names.count, maxVisible), id: \.self) { index in
                AvatarView(
                    name: names[index],
                    imageURL: imageURLs[safe: index] ?? nil,
                    size: size
                )
                .overlay(
                    Circle()
                        .stroke(Color.backgroundPrimary, lineWidth: 2)
                )
            }

            if names.count > maxVisible {
                ZStack {
                    Circle()
                        .fill(Color.backgroundTertiary)

                    Text("+\(names.count - maxVisible)")
                        .font(.caption2)
                        .fontWeight(.semibold)
                        .foregroundColor(.textSecondary)
                }
                .frame(width: size, height: size)
                .overlay(
                    Circle()
                        .stroke(Color.backgroundPrimary, lineWidth: 2)
                )
            }
        }
    }
}

// MARK: - Safe Array Extension

extension Array {
    subscript(safe index: Int) -> Element? {
        return indices.contains(index) ? self[index] : nil
    }
}

// MARK: - Preview

#Preview("Avatar Variants") {
    VStack(spacing: 30) {
        // Basic avatars
        HStack(spacing: 20) {
            AvatarView(name: "John Doe", imageURL: nil, size: Layout.avatarSmall)
            AvatarView(name: "Jane Smith", imageURL: nil, size: Layout.avatarMedium)
            AvatarView(name: "Bob Johnson", imageURL: nil, size: Layout.avatarLarge)
            AvatarView(name: "Alice Williams", imageURL: nil, size: Layout.avatarXLarge)
        }

        // Avatars with status
        HStack(spacing: 20) {
            AvatarWithStatus(name: "John Doe", imageURL: nil, isOnline: true)
            AvatarWithStatus(name: "Jane Smith", imageURL: nil, isOnline: false)
            AvatarWithStatus(name: "Bob Johnson", imageURL: nil, size: Layout.avatarLarge, isOnline: true)
        }

        // Avatar group
        AvatarGroup(
            names: ["John Doe", "Jane Smith", "Bob Johnson", "Alice Williams", "Charlie Brown"],
            imageURLs: [nil, nil, nil, nil, nil],
            size: Layout.avatarSmall
        )

        // Custom colors
        HStack(spacing: 20) {
            AvatarView(name: "Support Team", imageURL: nil, backgroundColor: .primary)
            AvatarView(name: "Marketing", imageURL: nil, backgroundColor: .tagPurple)
            AvatarView(name: "Sales", imageURL: nil, backgroundColor: .tagOrange)
        }
    }
    .padding()
    .background(Color.backgroundPrimary)
}
