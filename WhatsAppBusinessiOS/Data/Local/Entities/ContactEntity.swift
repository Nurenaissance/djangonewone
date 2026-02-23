//
//  ContactEntity.swift
//  WhatsAppBusinessiOS
//
//  SwiftData model for Contact entity
//

import Foundation
import SwiftData

@Model
final class ContactEntity {
    @Attribute(.unique) var id: String
    var name: String
    var phone: String
    var email: String?
    var address: String?
    var customFields: [String: String]
    var tags: [String]
    var lastMessage: String?
    var lastMessageTime: Date?
    var unreadCount: Int
    var tenantId: String
    var createdAt: Date
    var updatedAt: Date
    var needsSync: Bool

    @Relationship(deleteRule: .cascade, inverse: \MessageEntity.contact)
    var messages: [MessageEntity]

    init(
        id: String,
        name: String,
        phone: String,
        email: String? = nil,
        address: String? = nil,
        customFields: [String: String] = [:],
        tags: [String] = [],
        lastMessage: String? = nil,
        lastMessageTime: Date? = nil,
        unreadCount: Int = 0,
        tenantId: String,
        createdAt: Date = Date(),
        updatedAt: Date = Date(),
        needsSync: Bool = false
    ) {
        self.id = id
        self.name = name
        self.phone = phone
        self.email = email
        self.address = address
        self.customFields = customFields
        self.tags = tags
        self.lastMessage = lastMessage
        self.lastMessageTime = lastMessageTime
        self.unreadCount = unreadCount
        self.tenantId = tenantId
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.needsSync = needsSync
        self.messages = []
    }

    // MARK: - Update Methods

    func updateLastMessage(_ text: String, at time: Date) {
        self.lastMessage = text
        self.lastMessageTime = time
        self.updatedAt = Date()
    }

    func incrementUnreadCount() {
        self.unreadCount += 1
        self.updatedAt = Date()
    }

    func clearUnreadCount() {
        self.unreadCount = 0
        self.updatedAt = Date()
    }

    func markForSync() {
        self.needsSync = true
        self.updatedAt = Date()
    }

    func clearSyncFlag() {
        self.needsSync = false
    }
}

// MARK: - Contact Domain Model (for use in ViewModels)

struct Contact: Identifiable, Codable {
    let id: String
    var name: String
    var phone: String
    var email: String?
    var address: String?
    var customFields: [String: String]
    var tags: [String]
    var lastMessage: String?
    var lastMessageTime: Date?
    var unreadCount: Int
    var tenantId: String
    var createdAt: Date
    var updatedAt: Date

    init(
        id: String = UUID().uuidString,
        name: String,
        phone: String,
        email: String? = nil,
        address: String? = nil,
        customFields: [String: String] = [:],
        tags: [String] = [],
        lastMessage: String? = nil,
        lastMessageTime: Date? = nil,
        unreadCount: Int = 0,
        tenantId: String,
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.name = name
        self.phone = phone
        self.email = email
        self.address = address
        self.customFields = customFields
        self.tags = tags
        self.lastMessage = lastMessage
        self.lastMessageTime = lastMessageTime
        self.unreadCount = unreadCount
        self.tenantId = tenantId
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }

    // Convert from Entity
    init(from entity: ContactEntity) {
        self.id = entity.id
        self.name = entity.name
        self.phone = entity.phone
        self.email = entity.email
        self.address = entity.address
        self.customFields = entity.customFields
        self.tags = entity.tags
        self.lastMessage = entity.lastMessage
        self.lastMessageTime = entity.lastMessageTime
        self.unreadCount = entity.unreadCount
        self.tenantId = entity.tenantId
        self.createdAt = entity.createdAt
        self.updatedAt = entity.updatedAt
    }

    // Convert to Entity
    func toEntity() -> ContactEntity {
        return ContactEntity(
            id: id,
            name: name,
            phone: phone,
            email: email,
            address: address,
            customFields: customFields,
            tags: tags,
            lastMessage: lastMessage,
            lastMessageTime: lastMessageTime,
            unreadCount: unreadCount,
            tenantId: tenantId,
            createdAt: createdAt,
            updatedAt: updatedAt,
            needsSync: false
        )
    }
}

// MARK: - Helper Extensions

extension Contact {
    var initials: String {
        let components = name.split(separator: " ")
        if components.count >= 2 {
            return String(components[0].prefix(1) + components[1].prefix(1)).uppercased()
        } else {
            return String(name.prefix(2)).uppercased()
        }
    }

    var formattedPhone: String {
        // Format phone number (e.g., +1 (234) 567-8900)
        let cleaned = phone.filter { $0.isNumber }
        if cleaned.hasPrefix("91") && cleaned.count == 12 {
            // Indian format: +91 12345 67890
            let areaCode = cleaned.prefix(2)
            let firstPart = cleaned.dropFirst(2).prefix(5)
            let secondPart = cleaned.dropFirst(7)
            return "+\(areaCode) \(firstPart) \(secondPart)"
        }
        return phone
    }

    var lastMessagePreview: String {
        guard let message = lastMessage else {
            return "No messages yet"
        }
        return message.count > 50 ? String(message.prefix(50)) + "..." : message
    }
}
