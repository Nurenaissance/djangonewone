//
//  MessageEntity.swift
//  WhatsAppBusinessiOS
//
//  SwiftData model for Message entity
//

import Foundation
import SwiftData

@Model
final class MessageEntity {
    @Attribute(.unique) var id: String
    var text: String
    var sender: String
    var receiver: String
    var timestamp: Date
    var statusRaw: String
    var typeRaw: String
    var mediaURL: String?
    var thumbnailURL: String?
    var tenantId: String
    var needsSync: Bool

    @Relationship var contact: ContactEntity?

    var status: MessageStatus {
        get { MessageStatus(rawValue: statusRaw) ?? .pending }
        set { statusRaw = newValue.rawValue }
    }

    var type: MessageType {
        get { MessageType(rawValue: typeRaw) ?? .text }
        set { typeRaw = newValue.rawValue }
    }

    init(
        id: String,
        text: String,
        sender: String,
        receiver: String,
        timestamp: Date = Date(),
        status: MessageStatus = .pending,
        type: MessageType = .text,
        mediaURL: String? = nil,
        thumbnailURL: String? = nil,
        tenantId: String,
        needsSync: Bool = false
    ) {
        self.id = id
        self.text = text
        self.sender = sender
        self.receiver = receiver
        self.timestamp = timestamp
        self.statusRaw = status.rawValue
        self.typeRaw = type.rawValue
        self.mediaURL = mediaURL
        self.thumbnailURL = thumbnailURL
        self.tenantId = tenantId
        self.needsSync = needsSync
    }

    // MARK: - Update Methods

    func updateStatus(_ status: MessageStatus) {
        self.status = status
    }

    func markForSync() {
        self.needsSync = true
    }

    func clearSyncFlag() {
        self.needsSync = false
    }
}

// MARK: - Message Status

enum MessageStatus: String, Codable {
    case pending = "pending"
    case sent = "sent"
    case delivered = "delivered"
    case read = "read"
    case failed = "failed"

    var displayText: String {
        switch self {
        case .pending: return "Sending..."
        case .sent: return "Sent"
        case .delivered: return "Delivered"
        case .read: return "Read"
        case .failed: return "Failed"
        }
    }

    var iconName: String {
        switch self {
        case .pending: return "clock"
        case .sent: return "checkmark"
        case .delivered: return "checkmark.circle"
        case .read: return "checkmark.circle.fill"
        case .failed: return "exclamationmark.circle"
        }
    }
}

// MARK: - Message Type

enum MessageType: String, Codable {
    case text = "text"
    case image = "image"
    case video = "video"
    case audio = "audio"
    case document = "document"
    case template = "template"

    var iconName: String {
        switch self {
        case .text: return "text.bubble"
        case .image: return "photo"
        case .video: return "video"
        case .audio: return "waveform"
        case .document: return "doc"
        case .template: return "envelope"
        }
    }
}

// MARK: - Message Domain Model

struct Message: Identifiable, Codable {
    let id: String
    var text: String
    var sender: String
    var receiver: String
    var timestamp: Date
    var status: MessageStatus
    var type: MessageType
    var mediaURL: String?
    var thumbnailURL: String?
    var tenantId: String

    init(
        id: String = UUID().uuidString,
        text: String,
        sender: String,
        receiver: String,
        timestamp: Date = Date(),
        status: MessageStatus = .pending,
        type: MessageType = .text,
        mediaURL: String? = nil,
        thumbnailURL: String? = nil,
        tenantId: String
    ) {
        self.id = id
        self.text = text
        self.sender = sender
        self.receiver = receiver
        self.timestamp = timestamp
        self.status = status
        self.type = type
        self.mediaURL = mediaURL
        self.thumbnailURL = thumbnailURL
        self.tenantId = tenantId
    }

    // Convert from Entity
    init(from entity: MessageEntity) {
        self.id = entity.id
        self.text = entity.text
        self.sender = entity.sender
        self.receiver = entity.receiver
        self.timestamp = entity.timestamp
        self.status = entity.status
        self.type = entity.type
        self.mediaURL = entity.mediaURL
        self.thumbnailURL = entity.thumbnailURL
        self.tenantId = entity.tenantId
    }

    // Convert to Entity
    func toEntity() -> MessageEntity {
        return MessageEntity(
            id: id,
            text: text,
            sender: sender,
            receiver: receiver,
            timestamp: timestamp,
            status: status,
            type: type,
            mediaURL: mediaURL,
            thumbnailURL: thumbnailURL,
            tenantId: tenantId,
            needsSync: false
        )
    }
}

// MARK: - Helper Extensions

extension Message {
    var isFromCurrentUser: Bool {
        // Compare with stored user phone or check if sender is not the contact
        // For now, we'll check against the receiver
        return sender != receiver
    }

    var formattedTime: String {
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        return formatter.string(from: timestamp)
    }

    var formattedDate: String {
        let formatter = DateFormatter()
        let calendar = Calendar.current

        if calendar.isDateInToday(timestamp) {
            return "Today"
        } else if calendar.isDateInYesterday(timestamp) {
            return "Yesterday"
        } else if calendar.isDate(timestamp, equalTo: Date(), toGranularity: .weekOfYear) {
            formatter.dateFormat = "EEEE" // Day name
            return formatter.string(from: timestamp)
        } else {
            formatter.dateStyle = .medium
            return formatter.string(from: timestamp)
        }
    }

    var needsDateSeparator: Bool {
        // This will be determined by comparing with previous message in the list
        return true
    }
}
