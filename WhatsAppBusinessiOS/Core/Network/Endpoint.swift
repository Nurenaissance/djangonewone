//
//  Endpoint.swift
//  WhatsAppBusinessiOS
//
//  API endpoint definitions for Django, FastAPI, and Node.js backends
//

import Foundation

enum HTTPMethod: String {
    case get = "GET"
    case post = "POST"
    case put = "PUT"
    case patch = "PATCH"
    case delete = "DELETE"
}

enum Endpoint {
    // MARK: - Django Endpoints (Authentication & Contacts)
    case login(username: String, password: String)
    case refreshToken(refreshToken: String)
    case register(username: String, email: String, password: String)
    case fetchContacts(page: Int, limit: Int)
    case createContact(contact: ContactDTO)
    case updateContact(id: String, contact: ContactDTO)
    case deleteContact(id: String)
    case importContacts(contacts: [ContactDTO])

    // MARK: - FastAPI Endpoints (Analytics & Campaigns)
    case fetchAnalytics(timeRange: TimeRange)
    case fetchTemplates
    case fetchCampaignHistory(page: Int, limit: Int)
    case createCampaign(campaign: CampaignDTO)
    case fetchCampaignDetail(id: String)
    case fetchScheduledEvents
    case createScheduledEvent(event: ScheduledEventDTO)
    case deleteScheduledEvent(id: String)
    case fetchCatalog(page: Int, limit: Int)

    // MARK: - Node.js Endpoints (WhatsApp Messaging)
    case sendTextMessage(to: String, text: String)
    case sendTemplateMessage(to: String, templateId: String, parameters: [String])
    case sendImage(to: String, imageURL: String, caption: String?)
    case sendVideo(to: String, videoURL: String, caption: String?)
    case sendDocument(to: String, documentURL: String, filename: String)
    case uploadMedia(data: Data, type: MediaType)
    case fetchQRCode
    case checkConnectionStatus

    // MARK: - Base URLs

    var baseURL: String {
        switch self {
        case .login, .refreshToken, .register,
             .fetchContacts, .createContact, .updateContact, .deleteContact, .importContacts:
            return "https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net"

        case .fetchAnalytics, .fetchTemplates, .fetchCampaignHistory, .createCampaign, .fetchCampaignDetail,
             .fetchScheduledEvents, .createScheduledEvent, .deleteScheduledEvent, .fetchCatalog:
            return "https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net"

        case .sendTextMessage, .sendTemplateMessage, .sendImage, .sendVideo, .sendDocument,
             .uploadMedia, .fetchQRCode, .checkConnectionStatus:
            return "https://whatsappbotserver.azurewebsites.net"
        }
    }

    // MARK: - Paths

    var path: String {
        switch self {
        // Django
        case .login, .refreshToken:
            return "/oauth/token/"
        case .register:
            return "/api/auth/register/"
        case .fetchContacts, .createContact:
            return "/api/contacts/"
        case .updateContact(let id, _), .deleteContact(let id):
            return "/api/contacts/\(id)/"
        case .importContacts:
            return "/api/contacts/import/"

        // FastAPI
        case .fetchAnalytics:
            return "/analytics/campaign-stats"
        case .fetchTemplates:
            return "/whatsapp_tenant"
        case .fetchCampaignHistory, .createCampaign:
            return "/campaigns/history"
        case .fetchCampaignDetail(let id):
            return "/campaigns/\(id)"
        case .fetchScheduledEvents, .createScheduledEvent:
            return "/scheduled-events/"
        case .deleteScheduledEvent(let id):
            return "/scheduled-events/\(id)"
        case .fetchCatalog:
            return "/catalog/"

        // Node.js
        case .sendTextMessage:
            return "/send-text"
        case .sendTemplateMessage:
            return "/send-template"
        case .sendImage:
            return "/send-image"
        case .sendVideo:
            return "/send-video"
        case .sendDocument:
            return "/send-document"
        case .uploadMedia:
            return "/upload-media"
        case .fetchQRCode:
            return "/qr"
        case .checkConnectionStatus:
            return "/status"
        }
    }

    // MARK: - HTTP Method

    var method: HTTPMethod {
        switch self {
        case .login, .refreshToken, .register, .createContact, .importContacts,
             .createCampaign, .createScheduledEvent, .sendTextMessage, .sendTemplateMessage,
             .sendImage, .sendVideo, .sendDocument, .uploadMedia:
            return .post

        case .updateContact:
            return .put

        case .deleteContact, .deleteScheduledEvent:
            return .delete

        default:
            return .get
        }
    }

    // MARK: - Requires Authentication

    var requiresAuth: Bool {
        switch self {
        case .login, .register:
            return false
        default:
            return true
        }
    }

    // MARK: - Query Parameters

    var queryItems: [URLQueryItem]? {
        switch self {
        case .fetchContacts(let page, let limit):
            return [
                URLQueryItem(name: "page", value: "\(page)"),
                URLQueryItem(name: "limit", value: "\(limit)")
            ]

        case .fetchAnalytics(let timeRange):
            let days = timeRange.days
            return [
                URLQueryItem(name: "days", value: "\(days)")
            ]

        case .fetchCampaignHistory(let page, let limit):
            return [
                URLQueryItem(name: "page", value: "\(page)"),
                URLQueryItem(name: "limit", value: "\(limit)")
            ]

        case .fetchCatalog(let page, let limit):
            return [
                URLQueryItem(name: "page", value: "\(page)"),
                URLQueryItem(name: "limit", value: "\(limit)")
            ]

        default:
            return nil
        }
    }

    // MARK: - Request Body

    func body() throws -> Data? {
        switch self {
        case .login(let username, let password):
            let params = [
                "grant_type": "password",
                "username": username,
                "password": password
            ]
            return try JSONSerialization.data(withJSONObject: params)

        case .refreshToken(let refreshToken):
            let params = [
                "grant_type": "refresh_token",
                "refresh_token": refreshToken
            ]
            return try JSONSerialization.data(withJSONObject: params)

        case .register(let username, let email, let password):
            let params = [
                "username": username,
                "email": email,
                "password": password
            ]
            return try JSONEncoder().encode(params)

        case .createContact(let contact), .updateContact(_, let contact):
            return try JSONEncoder().encode(contact)

        case .importContacts(let contacts):
            return try JSONEncoder().encode(["contacts": contacts])

        case .createCampaign(let campaign):
            return try JSONEncoder().encode(campaign)

        case .createScheduledEvent(let event):
            return try JSONEncoder().encode(event)

        case .sendTextMessage(let to, let text):
            let params = ["to": to, "text": text]
            return try JSONEncoder().encode(params)

        case .sendTemplateMessage(let to, let templateId, let parameters):
            let params: [String: Any] = [
                "to": to,
                "template_id": templateId,
                "parameters": parameters
            ]
            return try JSONSerialization.data(withJSONObject: params)

        case .sendImage(let to, let imageURL, let caption):
            var params: [String: Any] = ["to": to, "image_url": imageURL]
            if let caption = caption {
                params["caption"] = caption
            }
            return try JSONSerialization.data(withJSONObject: params)

        case .sendVideo(let to, let videoURL, let caption):
            var params: [String: Any] = ["to": to, "video_url": videoURL]
            if let caption = caption {
                params["caption"] = caption
            }
            return try JSONSerialization.data(withJSONObject: params)

        case .sendDocument(let to, let documentURL, let filename):
            let params: [String: Any] = [
                "to": to,
                "document_url": documentURL,
                "filename": filename
            ]
            return try JSONSerialization.data(withJSONObject: params)

        case .uploadMedia(let data, let type):
            // For multipart/form-data, return raw data
            // The APIClient will handle multipart encoding
            return data

        default:
            return nil
        }
    }

    // MARK: - Convert to URLRequest

    func asURLRequest() throws -> URLRequest {
        guard var components = URLComponents(string: baseURL + path) else {
            throw NetworkError.invalidURL
        }

        components.queryItems = queryItems

        guard let url = components.url else {
            throw NetworkError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.timeoutInterval = 30

        // Add body if needed
        if let bodyData = try body() {
            request.httpBody = bodyData
        }

        return request
    }
}

// MARK: - Supporting Types

enum TimeRange {
    case last7Days
    case last30Days
    case last90Days
    case custom(days: Int)

    var days: Int {
        switch self {
        case .last7Days: return 7
        case .last30Days: return 30
        case .last90Days: return 90
        case .custom(let days): return days
        }
    }
}

enum MediaType: String {
    case image
    case video
    case audio
    case document
}

// MARK: - DTOs (Data Transfer Objects)
// These will be defined in separate files, but included here as placeholders

struct ContactDTO: Codable {
    let id: String?
    let name: String
    let phone: String
    let email: String?
    let address: String?
    let customFields: [String: String]?
    let tags: [String]?

    enum CodingKeys: String, CodingKey {
        case id, name, phone, email, address
        case customFields = "custom_field"
        case tags
    }
}

struct CampaignDTO: Codable {
    let id: String?
    let name: String
    let templateId: String
    let recipientPhones: [String]
    let scheduledTime: Date?

    enum CodingKeys: String, CodingKey {
        case id, name
        case templateId = "template_id"
        case recipientPhones = "recipient_phones"
        case scheduledTime = "scheduled_time"
    }
}

struct ScheduledEventDTO: Codable {
    let id: String?
    let templateId: String
    let recipientPhones: [String]
    let scheduledTime: Date

    enum CodingKeys: String, CodingKey {
        case id
        case templateId = "template_id"
        case recipientPhones = "recipient_phones"
        case scheduledTime = "scheduled_time"
    }
}
