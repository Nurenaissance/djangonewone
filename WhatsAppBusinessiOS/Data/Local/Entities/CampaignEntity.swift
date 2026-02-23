//
//  CampaignEntity.swift
//  WhatsAppBusinessiOS
//
//  SwiftData model for Campaign entity
//

import Foundation
import SwiftData

@Model
final class CampaignEntity {
    @Attribute(.unique) var id: String
    var name: String
    var templateId: String
    var templateName: String
    var recipientPhones: [String]
    var scheduledTime: Date?
    var statusRaw: String
    var totalSent: Int
    var delivered: Int
    var read: Int
    var failed: Int
    var tenantId: String
    var createdAt: Date
    var updatedAt: Date

    var status: CampaignStatus {
        get { CampaignStatus(rawValue: statusRaw) ?? .draft }
        set { statusRaw = newValue.rawValue }
    }

    var stats: CampaignStats {
        CampaignStats(
            totalSent: totalSent,
            delivered: delivered,
            read: read,
            failed: failed
        )
    }

    init(
        id: String,
        name: String,
        templateId: String,
        templateName: String,
        recipientPhones: [String],
        scheduledTime: Date? = nil,
        status: CampaignStatus = .draft,
        totalSent: Int = 0,
        delivered: Int = 0,
        read: Int = 0,
        failed: Int = 0,
        tenantId: String,
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.name = name
        self.templateId = templateId
        self.templateName = templateName
        self.recipientPhones = recipientPhones
        self.scheduledTime = scheduledTime
        self.statusRaw = status.rawValue
        self.totalSent = totalSent
        self.delivered = delivered
        self.read = read
        self.failed = failed
        self.tenantId = tenantId
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }

    // MARK: - Update Methods

    func updateStats(sent: Int, delivered: Int, read: Int, failed: Int) {
        self.totalSent = sent
        self.delivered = delivered
        self.read = read
        self.failed = failed
        self.updatedAt = Date()
    }

    func updateStatus(_ status: CampaignStatus) {
        self.status = status
        self.updatedAt = Date()
    }
}

// MARK: - Campaign Status

enum CampaignStatus: String, Codable {
    case draft = "draft"
    case scheduled = "scheduled"
    case sending = "sending"
    case completed = "completed"
    case failed = "failed"
    case cancelled = "cancelled"

    var displayText: String {
        switch self {
        case .draft: return "Draft"
        case .scheduled: return "Scheduled"
        case .sending: return "Sending"
        case .completed: return "Completed"
        case .failed: return "Failed"
        case .cancelled: return "Cancelled"
        }
    }

    var iconName: String {
        switch self {
        case .draft: return "doc.text"
        case .scheduled: return "clock"
        case .sending: return "paperplane"
        case .completed: return "checkmark.circle.fill"
        case .failed: return "exclamationmark.circle.fill"
        case .cancelled: return "xmark.circle.fill"
        }
    }

    var color: String {
        switch self {
        case .draft: return "gray"
        case .scheduled: return "blue"
        case .sending: return "orange"
        case .completed: return "green"
        case .failed: return "red"
        case .cancelled: return "gray"
        }
    }
}

// MARK: - Campaign Stats

struct CampaignStats: Codable {
    var totalSent: Int
    var delivered: Int
    var read: Int
    var failed: Int

    var deliveredRate: Double {
        guard totalSent > 0 else { return 0 }
        return Double(delivered) / Double(totalSent) * 100
    }

    var readRate: Double {
        guard delivered > 0 else { return 0 }
        return Double(read) / Double(delivered) * 100
    }

    var failedRate: Double {
        guard totalSent > 0 else { return 0 }
        return Double(failed) / Double(totalSent) * 100
    }

    var successRate: Double {
        guard totalSent > 0 else { return 0 }
        return Double(delivered + read) / Double(totalSent) * 100
    }
}

// MARK: - Campaign Domain Model

struct Campaign: Identifiable, Codable {
    let id: String
    var name: String
    var templateId: String
    var templateName: String
    var recipientPhones: [String]
    var scheduledTime: Date?
    var status: CampaignStatus
    var stats: CampaignStats
    var tenantId: String
    var createdAt: Date
    var updatedAt: Date

    init(
        id: String = UUID().uuidString,
        name: String,
        templateId: String,
        templateName: String,
        recipientPhones: [String],
        scheduledTime: Date? = nil,
        status: CampaignStatus = .draft,
        stats: CampaignStats = CampaignStats(totalSent: 0, delivered: 0, read: 0, failed: 0),
        tenantId: String,
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.name = name
        self.templateId = templateId
        self.templateName = templateName
        self.recipientPhones = recipientPhones
        self.scheduledTime = scheduledTime
        self.status = status
        self.stats = stats
        self.tenantId = tenantId
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }

    // Convert from Entity
    init(from entity: CampaignEntity) {
        self.id = entity.id
        self.name = entity.name
        self.templateId = entity.templateId
        self.templateName = entity.templateName
        self.recipientPhones = entity.recipientPhones
        self.scheduledTime = entity.scheduledTime
        self.status = entity.status
        self.stats = entity.stats
        self.tenantId = entity.tenantId
        self.createdAt = entity.createdAt
        self.updatedAt = entity.updatedAt
    }

    // Convert to Entity
    func toEntity() -> CampaignEntity {
        return CampaignEntity(
            id: id,
            name: name,
            templateId: templateId,
            templateName: templateName,
            recipientPhones: recipientPhones,
            scheduledTime: scheduledTime,
            status: status,
            totalSent: stats.totalSent,
            delivered: stats.delivered,
            read: stats.read,
            failed: stats.failed,
            tenantId: tenantId,
            createdAt: createdAt,
            updatedAt: updatedAt
        )
    }
}

// MARK: - Helper Extensions

extension Campaign {
    var recipientCount: Int {
        return recipientPhones.count
    }

    var formattedScheduledTime: String? {
        guard let time = scheduledTime else { return nil }

        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: time)
    }

    var isScheduled: Bool {
        return scheduledTime != nil && status == .scheduled
    }

    var canEdit: Bool {
        return status == .draft
    }

    var canCancel: Bool {
        return status == .scheduled || status == .sending
    }

    var progress: Double {
        guard recipientCount > 0 else { return 0 }
        return Double(stats.totalSent) / Double(recipientCount)
    }
}
