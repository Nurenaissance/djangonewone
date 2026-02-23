//
//  MessageBubble.swift
//  WhatsAppBusinessiOS
//
//  WhatsApp-style message bubble component
//

import SwiftUI

struct MessageBubble: View {
    let message: Message
    let isFromCurrentUser: Bool

    var body: some View {
        HStack(alignment: .bottom, spacing: 8) {
            if isFromCurrentUser {
                Spacer(minLength: 60)
            }

            VStack(alignment: isFromCurrentUser ? .trailing : .leading, spacing: 4) {
                // Message content
                MessageContent(message: message)
                    .padding(Spacing.messageBubblePadding)
                    .background(bubbleColor)
                    .foregroundColor(textColor)
                    .cornerRadius(CornerRadius.messageBubble, corners: bubbleCorners)

                // Timestamp and status
                HStack(spacing: 4) {
                    Text(message.formattedTime)
                        .font(.timestamp)
                        .foregroundColor(.textSecondary)

                    if isFromCurrentUser {
                        MessageStatusIcon(status: message.status)
                    }
                }
                .padding(.horizontal, 4)
            }

            if !isFromCurrentUser {
                Spacer(minLength: 60)
            }
        }
        .padding(.horizontal, Spacing.screenPadding)
        .padding(.vertical, 2)
    }

    // MARK: - Computed Properties

    private var bubbleColor: Color {
        isFromCurrentUser ? .sentBubble : .receivedBubble
    }

    private var textColor: Color {
        isFromCurrentUser ? .sentBubbleText : .receivedBubbleText
    }

    private var bubbleCorners: UIRectCorner {
        if isFromCurrentUser {
            return [.topLeft, .topRight, .bottomLeft]
        } else {
            return [.topLeft, .topRight, .bottomRight]
        }
    }
}

// MARK: - Message Content

struct MessageContent: View {
    let message: Message

    var body: some View {
        switch message.type {
        case .text:
            Text(message.text)
                .font(.messageBubble)
                .fixedSize(horizontal: false, vertical: true)

        case .image:
            ImageMessageContent(url: message.mediaURL, caption: message.text)

        case .video:
            VideoMessageContent(url: message.mediaURL, caption: message.text)

        case .audio:
            AudioMessageContent(url: message.mediaURL)

        case .document:
            DocumentMessageContent(url: message.mediaURL, filename: message.text)

        case .template:
            Text(message.text)
                .font(.messageBubble)
                .italic()
        }
    }
}

// MARK: - Image Message

struct ImageMessageContent: View {
    let url: String?
    let caption: String

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            if let urlString = url, let imageURL = URL(string: urlString) {
                AsyncImage(url: imageURL) { phase in
                    switch phase {
                    case .empty:
                        ProgressView()
                            .frame(width: 200, height: 200)
                    case .success(let image):
                        image
                            .resizable()
                            .aspectRatio(contentMode: .fill)
                            .frame(maxWidth: 250, maxHeight: 300)
                            .clipped()
                            .cornerRadius(8)
                    case .failure:
                        Image(systemName: "photo")
                            .font(.largeTitle)
                            .frame(width: 200, height: 200)
                            .background(Color.backgroundTertiary)
                            .cornerRadius(8)
                    @unknown default:
                        EmptyView()
                    }
                }
            }

            if !caption.isEmpty {
                Text(caption)
                    .font(.messageBubble)
            }
        }
    }
}

// MARK: - Video Message

struct VideoMessageContent: View {
    let url: String?
    let caption: String

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            ZStack {
                Rectangle()
                    .fill(Color.backgroundTertiary)
                    .frame(width: 250, height: 200)
                    .cornerRadius(8)

                Image(systemName: "play.circle.fill")
                    .font(.system(size: 50))
                    .foregroundColor(.white)
                    .shadow(radius: 2)
            }

            if !caption.isEmpty {
                Text(caption)
                    .font(.messageBubble)
            }
        }
    }
}

// MARK: - Audio Message

struct AudioMessageContent: View {
    let url: String?

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: "waveform")
                .font(.title3)

            // Waveform placeholder
            HStack(spacing: 2) {
                ForEach(0..<20, id: \.self) { _ in
                    RoundedRectangle(cornerRadius: 2)
                        .fill(Color.primary.opacity(0.3))
                        .frame(width: 3, height: CGFloat.random(in: 10...30))
                }
            }

            Text("0:24")
                .font(.caption1)
                .monospacedDigit()
        }
        .frame(width: 250)
    }
}

// MARK: - Document Message

struct DocumentMessageContent: View {
    let url: String?
    let filename: String

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: "doc.fill")
                .font(.title2)
                .foregroundColor(.primary)

            VStack(alignment: .leading, spacing: 2) {
                Text(filename)
                    .font(.body)
                    .lineLimit(1)

                Text("PDF Document")
                    .font(.caption1)
                    .foregroundColor(.secondary)
            }

            Spacer()

            Image(systemName: "arrow.down.circle")
                .font(.title3)
        }
        .frame(width: 250)
    }
}

// MARK: - Message Status Icon

struct MessageStatusIcon: View {
    let status: MessageStatus

    var body: some View {
        Image(systemName: status.iconName)
            .font(.caption2)
            .foregroundColor(Color.colorForMessageStatus(status))
    }
}

// MARK: - Custom Corner Radius

extension View {
    func cornerRadius(_ radius: CGFloat, corners: UIRectCorner) -> some View {
        clipShape(RoundedCorner(radius: radius, corners: corners))
    }
}

struct RoundedCorner: Shape {
    var radius: CGFloat = .infinity
    var corners: UIRectCorner = .allCorners

    func path(in rect: CGRect) -> Path {
        let path = UIBezierPath(
            roundedRect: rect,
            byRoundingCorners: corners,
            cornerRadii: CGSize(width: radius, height: radius)
        )
        return Path(path.cgPath)
    }
}

// MARK: - Preview

#Preview {
    VStack(spacing: 16) {
        MessageBubble(
            message: Message(
                text: "Hello! How are you?",
                sender: "other",
                receiver: "me",
                status: .read,
                tenantId: "1"
            ),
            isFromCurrentUser: false
        )

        MessageBubble(
            message: Message(
                text: "I'm doing great, thanks for asking!",
                sender: "me",
                receiver: "other",
                status: .delivered,
                tenantId: "1"
            ),
            isFromCurrentUser: true
        )

        MessageBubble(
            message: Message(
                text: "This is a longer message to test how the bubble expands with more text. It should wrap nicely and maintain good readability.",
                sender: "other",
                receiver: "me",
                status: .read,
                tenantId: "1"
            ),
            isFromCurrentUser: false
        )
    }
    .padding()
    .background(Color.backgroundPrimary)
}
