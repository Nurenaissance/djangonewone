//
//  SocketIOManager.swift
//  WhatsAppBusinessiOS
//
//  Real-time messaging with Socket.IO
//  NOTE: This file requires the SocketIO-Client-Swift package to be installed
//

import Foundation
import Combine

// Note: Uncomment these imports when the SocketIO package is installed
// import SocketIO

@MainActor
class SocketIOManager: ObservableObject {
    static let shared = SocketIOManager()

    // Socket.IO properties (will use when package is installed)
    // private var manager: SocketManager!
    // private var socket: SocketIOClient!

    @Published var isConnected = false
    @Published var connectionStatus: ConnectionStatus = .disconnected

    // Publishers for real-time events
    let newMessageSubject = PassthroughSubject<Message, Never>()
    let messageStatusSubject = PassthroughSubject<MessageStatusUpdate, Never>()
    let qrCodeSubject = PassthroughSubject<String, Never>()
    let typingIndicatorSubject = PassthroughSubject<TypingIndicator, Never>()

    private let baseURL = "https://whatsappbotserver.azurewebsites.net"
    private var reconnectAttempts = 0
    private let maxReconnectAttempts = 10

    private init() {}

    // MARK: - Connection

    func connect(token: String, tenantId: String) {
        /* TODO: Implement when SocketIO package is installed

        manager = SocketManager(
            socketURL: URL(string: baseURL)!,
            config: [
                .log(false),
                .compress,
                .forceWebsockets(true),
                .reconnects(true),
                .reconnectAttempts(maxReconnectAttempts),
                .reconnectWait(2),
                .extraHeaders(["Authorization": "Bearer \(token)"])
            ]
        )

        socket = manager.defaultSocket

        setupEventHandlers(tenantId: tenantId)
        socket.connect()

        */

        // Temporary mock implementation for development
        print("🔌 Socket.IO: Would connect with token: \(token.prefix(20))...")
        print("🏢 Tenant ID: \(tenantId)")

        // Simulate connection
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            self.isConnected = true
            self.connectionStatus = .connected
            print("✅ Socket.IO: Connected (mock)")
        }
    }

    func disconnect() {
        /* TODO: Implement when SocketIO package is installed
        socket?.disconnect()
        */

        isConnected = false
        connectionStatus = .disconnected
        print("🔌 Socket.IO: Disconnected")
    }

    // MARK: - Event Handlers

    private func setupEventHandlers(tenantId: String) {
        /* TODO: Implement when SocketIO package is installed

        // Connection events
        socket.on(clientEvent: .connect) { [weak self] data, ack in
            guard let self = self else { return }
            Task { @MainActor in
                self.isConnected = true
                self.connectionStatus = .connected
                self.reconnectAttempts = 0

                // Join tenant room
                self.socket.emit("join", tenantId)

                print("✅ Socket.IO: Connected")
            }
        }

        socket.on(clientEvent: .disconnect) { [weak self] data, ack in
            guard let self = self else { return }
            Task { @MainActor in
                self.isConnected = false
                self.connectionStatus = .disconnected
                print("🔌 Socket.IO: Disconnected")
            }
        }

        socket.on(clientEvent: .reconnect) { [weak self] data, ack in
            guard let self = self else { return }
            Task { @MainActor in
                self.reconnectAttempts += 1
                self.connectionStatus = .reconnecting
                print("🔄 Socket.IO: Reconnecting (attempt \(self.reconnectAttempts))")
            }
        }

        socket.on(clientEvent: .error) { data, ack in
            print("❌ Socket.IO Error: \(data)")
        }

        // Custom events
        socket.on("new-message") { [weak self] data, ack in
            self?.handleNewMessage(data)
        }

        socket.on("message-status") { [weak self] data, ack in
            self?.handleMessageStatus(data)
        }

        socket.on("qr-update") { [weak self] data, ack in
            self?.handleQRUpdate(data)
        }

        socket.on("typing") { [weak self] data, ack in
            self?.handleTypingIndicator(data)
        }

        */
    }

    // MARK: - Message Handlers

    private func handleNewMessage(_ data: [Any]) {
        guard let messageData = data.first as? [String: Any] else {
            print("❌ Invalid message data")
            return
        }

        Task { @MainActor in
            do {
                // Parse message
                let jsonData = try JSONSerialization.data(withJSONObject: messageData)
                let decoder = JSONDecoder()
                decoder.dateDecodingStrategy = .iso8601

                let message = try decoder.decode(Message.self, from: jsonData)

                // Publish to subscribers
                newMessageSubject.send(message)

                // Save to local database
                let entity = message.toEntity()
                DataController.shared.insertMessage(entity)

                print("📨 New message received: \(message.text)")
            } catch {
                print("❌ Failed to parse message: \(error)")
            }
        }
    }

    private func handleMessageStatus(_ data: [Any]) {
        guard let statusData = data.first as? [String: Any],
              let messageId = statusData["messageId"] as? String,
              let statusString = statusData["status"] as? String,
              let status = MessageStatus(rawValue: statusString) else {
            print("❌ Invalid status data")
            return
        }

        Task { @MainActor in
            let update = MessageStatusUpdate(messageId: messageId, status: status)
            messageStatusSubject.send(update)

            print("📊 Message status updated: \(messageId) -> \(status.displayText)")
        }
    }

    private func handleQRUpdate(_ data: [Any]) {
        guard let qrData = data.first as? [String: Any],
              let qrCode = qrData["qr"] as? String else {
            print("❌ Invalid QR data")
            return
        }

        Task { @MainActor in
            qrCodeSubject.send(qrCode)
            print("📱 QR Code updated")
        }
    }

    private func handleTypingIndicator(_ data: [Any]) {
        guard let typingData = data.first as? [String: Any],
              let phone = typingData["phone"] as? String,
              let isTyping = typingData["isTyping"] as? Bool else {
            return
        }

        Task { @MainActor in
            let indicator = TypingIndicator(phone: phone, isTyping: isTyping)
            typingIndicatorSubject.send(indicator)
        }
    }

    // MARK: - Send Events

    func sendMessage(to: String, text: String) {
        /* TODO: Implement when SocketIO package is installed

        socket.emit("send-message", [
            "to": to,
            "text": text,
            "tenant_id": UserDefaults.standard.tenantId ?? ""
        ])

        */

        print("📤 Sending message to \(to): \(text)")
    }

    func sendTypingIndicator(to: String, isTyping: Bool) {
        /* TODO: Implement when SocketIO package is installed

        socket.emit("typing", [
            "to": to,
            "isTyping": isTyping,
            "tenant_id": UserDefaults.standard.tenantId ?? ""
        ])

        */

        print("⌨️ Typing indicator: \(isTyping)")
    }

    func markAsRead(messageId: String) {
        /* TODO: Implement when SocketIO package is installed

        socket.emit("mark-read", [
            "messageId": messageId,
            "tenant_id": UserDefaults.standard.tenantId ?? ""
        ])

        */

        print("✅ Marked as read: \(messageId)")
    }
}

// MARK: - Supporting Types

enum ConnectionStatus {
    case disconnected
    case connecting
    case connected
    case reconnecting
    case failed

    var displayText: String {
        switch self {
        case .disconnected: return "Disconnected"
        case .connecting: return "Connecting..."
        case .connected: return "Connected"
        case .reconnecting: return "Reconnecting..."
        case .failed: return "Connection Failed"
        }
    }

    var iconName: String {
        switch self {
        case .disconnected: return "wifi.slash"
        case .connecting, .reconnecting: return "wifi.exclamationmark"
        case .connected: return "wifi"
        case .failed: return "wifi.slash"
        }
    }
}

struct MessageStatusUpdate {
    let messageId: String
    let status: MessageStatus
}

struct TypingIndicator {
    let phone: String
    let isTyping: Bool
}

// MARK: - Message DTO for Socket.IO

extension Message {
    // Custom decoder for Socket.IO message format
    init(from socketData: [String: Any]) throws {
        guard let id = socketData["id"] as? String ?? socketData["wamid"] as? String,
              let text = socketData["message"] as? String ?? socketData["text"] as? String,
              let sender = socketData["sender"] as? String ?? socketData["from"] as? String,
              let receiver = socketData["receiver"] as? String ?? socketData["to"] as? String else {
            throw NSError(domain: "SocketIOMessage", code: 1, userInfo: [NSLocalizedDescriptionKey: "Invalid message data"])
        }

        let timestamp: Date
        if let timestampString = socketData["timestamp"] as? String,
           let date = ISO8601DateFormatter().date(from: timestampString) {
            timestamp = date
        } else {
            timestamp = Date()
        }

        let statusString = socketData["status"] as? String ?? "sent"
        let status = MessageStatus(rawValue: statusString) ?? .sent

        let typeString = socketData["type"] as? String ?? "text"
        let type = MessageType(rawValue: typeString) ?? .text

        let mediaURL = socketData["mediaUrl"] as? String ?? socketData["media_url"] as? String
        let thumbnailURL = socketData["thumbnailUrl"] as? String ?? socketData["thumbnail_url"] as? String
        let tenantId = socketData["tenantId"] as? String ?? socketData["tenant_id"] as? String ?? ""

        self.init(
            id: id,
            text: text,
            sender: sender,
            receiver: receiver,
            timestamp: timestamp,
            status: status,
            type: type,
            mediaURL: mediaURL,
            thumbnailURL: thumbnailURL,
            tenantId: tenantId
        )
    }
}
