//
//  DataController.swift
//  WhatsAppBusinessiOS
//
//  SwiftData setup and configuration
//

import Foundation
import SwiftData

@MainActor
class DataController {
    static let shared = DataController()

    let container: ModelContainer
    let context: ModelContext

    private init() {
        // Define the schema with all models
        let schema = Schema([
            ContactEntity.self,
            MessageEntity.self,
            CampaignEntity.self
        ])

        // Configure the model container
        let config = ModelConfiguration(
            schema: schema,
            isStoredInMemoryOnly: false,
            allowsSave: true,
            cloudKitDatabase: .none  // Can enable iCloud sync later
        )

        do {
            container = try ModelContainer(for: schema, configurations: [config])
            context = ModelContext(container)
            context.autosaveEnabled = true

            print("✅ SwiftData initialized successfully")
        } catch {
            fatalError("Failed to create ModelContainer: \(error)")
        }
    }

    // MARK: - Save

    func save() {
        do {
            try context.save()
        } catch {
            print("❌ Failed to save context: \(error)")
        }
    }

    // MARK: - Contact Operations

    func fetchContacts(tenantId: String) -> [ContactEntity] {
        let descriptor = FetchDescriptor<ContactEntity>(
            predicate: #Predicate { $0.tenantId == tenantId },
            sortBy: [SortDescriptor(\.updatedAt, order: .reverse)]
        )

        do {
            return try context.fetch(descriptor)
        } catch {
            print("❌ Failed to fetch contacts: \(error)")
            return []
        }
    }

    func fetchContact(id: String) -> ContactEntity? {
        let descriptor = FetchDescriptor<ContactEntity>(
            predicate: #Predicate { $0.id == id }
        )

        do {
            return try context.fetch(descriptor).first
        } catch {
            print("❌ Failed to fetch contact: \(error)")
            return nil
        }
    }

    func insertContact(_ contact: ContactEntity) {
        context.insert(contact)
        save()
    }

    func deleteContact(_ contact: ContactEntity) {
        context.delete(contact)
        save()
    }

    // MARK: - Message Operations

    func fetchMessages(for contactPhone: String, tenantId: String, limit: Int = 100) -> [MessageEntity] {
        let descriptor = FetchDescriptor<MessageEntity>(
            predicate: #Predicate { message in
                (message.sender == contactPhone || message.receiver == contactPhone) &&
                message.tenantId == tenantId
            },
            sortBy: [SortDescriptor(\.timestamp, order: .reverse)]
        )

        do {
            var messages = try context.fetch(descriptor)
            if messages.count > limit {
                messages = Array(messages.prefix(limit))
            }
            return messages
        } catch {
            print("❌ Failed to fetch messages: \(error)")
            return []
        }
    }

    func insertMessage(_ message: MessageEntity) {
        context.insert(message)

        // Update contact's last message
        if let contact = message.contact {
            contact.updateLastMessage(message.text, at: message.timestamp)
        }

        save()
    }

    func deleteMessage(_ message: MessageEntity) {
        context.delete(message)
        save()
    }

    // MARK: - Campaign Operations

    func fetchCampaigns(tenantId: String) -> [CampaignEntity] {
        let descriptor = FetchDescriptor<CampaignEntity>(
            predicate: #Predicate { $0.tenantId == tenantId },
            sortBy: [SortDescriptor(\.createdAt, order: .reverse)]
        )

        do {
            return try context.fetch(descriptor)
        } catch {
            print("❌ Failed to fetch campaigns: \(error)")
            return []
        }
    }

    func fetchCampaign(id: String) -> CampaignEntity? {
        let descriptor = FetchDescriptor<CampaignEntity>(
            predicate: #Predicate { $0.id == id }
        )

        do {
            return try context.fetch(descriptor).first
        } catch {
            print("❌ Failed to fetch campaign: \(error)")
            return nil
        }
    }

    func insertCampaign(_ campaign: CampaignEntity) {
        context.insert(campaign)
        save()
    }

    func deleteCampaign(_ campaign: CampaignEntity) {
        context.delete(campaign)
        save()
    }

    // MARK: - Sync Operations

    func fetchPendingSyncContacts(tenantId: String) -> [ContactEntity] {
        let descriptor = FetchDescriptor<ContactEntity>(
            predicate: #Predicate { $0.tenantId == tenantId && $0.needsSync == true }
        )

        do {
            return try context.fetch(descriptor)
        } catch {
            print("❌ Failed to fetch pending sync contacts: \(error)")
            return []
        }
    }

    func fetchPendingSyncMessages(tenantId: String) -> [MessageEntity] {
        let descriptor = FetchDescriptor<MessageEntity>(
            predicate: #Predicate { $0.tenantId == tenantId && $0.needsSync == true }
        )

        do {
            return try context.fetch(descriptor)
        } catch {
            print("❌ Failed to fetch pending sync messages: \(error)")
            return []
        }
    }

    // MARK: - Clear Data

    func clearAllData() {
        do {
            // Delete all contacts (cascade will delete messages)
            try context.delete(model: ContactEntity.self)
            try context.delete(model: CampaignEntity.self)

            save()
            print("✅ All data cleared")
        } catch {
            print("❌ Failed to clear data: \(error)")
        }
    }

    func clearTenantData(tenantId: String) {
        do {
            // Delete all data for specific tenant
            try context.delete(
                model: ContactEntity.self,
                where: #Predicate { $0.tenantId == tenantId }
            )
            try context.delete(
                model: MessageEntity.self,
                where: #Predicate { $0.tenantId == tenantId }
            )
            try context.delete(
                model: CampaignEntity.self,
                where: #Predicate { $0.tenantId == tenantId }
            )

            save()
            print("✅ Tenant data cleared for: \(tenantId)")
        } catch {
            print("❌ Failed to clear tenant data: \(error)")
        }
    }

    // MARK: - Search

    func searchContacts(query: String, tenantId: String) -> [ContactEntity] {
        let lowercasedQuery = query.lowercased()

        let descriptor = FetchDescriptor<ContactEntity>(
            predicate: #Predicate { contact in
                contact.tenantId == tenantId &&
                (contact.name.lowercased().contains(lowercasedQuery) ||
                 contact.phone.contains(lowercasedQuery) ||
                 (contact.email?.lowercased().contains(lowercasedQuery) ?? false))
            },
            sortBy: [SortDescriptor(\.name)]
        )

        do {
            return try context.fetch(descriptor)
        } catch {
            print("❌ Failed to search contacts: \(error)")
            return []
        }
    }
}
