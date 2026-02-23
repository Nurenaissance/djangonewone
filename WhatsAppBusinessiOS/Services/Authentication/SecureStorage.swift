//
//  SecureStorage.swift
//  WhatsAppBusinessiOS
//
//  Keychain wrapper for secure token storage
//

import Foundation
import Security

class SecureStorage {
    static let shared = SecureStorage()

    private let serviceName = "com.whatsappbusiness.ios"

    private init() {}

    // MARK: - Token Storage

    var accessToken: String? {
        get { retrieveString(forKey: "access_token") }
        set {
            if let value = newValue {
                save(value, forKey: "access_token")
            } else {
                delete(forKey: "access_token")
            }
        }
    }

    var refreshToken: String? {
        get { retrieveString(forKey: "refresh_token") }
        set {
            if let value = newValue {
                save(value, forKey: "refresh_token")
            } else {
                delete(forKey: "refresh_token")
            }
        }
    }

    var tokenExpiresAt: Date? {
        get {
            guard let timestamp = retrieveString(forKey: "token_expires_at"),
                  let timeInterval = TimeInterval(timestamp) else {
                return nil
            }
            return Date(timeIntervalSince1970: timeInterval)
        }
        set {
            if let value = newValue {
                let timestamp = String(value.timeIntervalSince1970)
                save(timestamp, forKey: "token_expires_at")
            } else {
                delete(forKey: "token_expires_at")
            }
        }
    }

    // MARK: - Save Tokens

    func saveTokens(accessToken: String, refreshToken: String, expiresIn: Int) {
        self.accessToken = accessToken
        self.refreshToken = refreshToken

        // Calculate expiry time (expiresIn is in seconds)
        let expiryDate = Date().addingTimeInterval(TimeInterval(expiresIn))
        self.tokenExpiresAt = expiryDate
    }

    // MARK: - Clear Tokens

    func clearTokens() {
        accessToken = nil
        refreshToken = nil
        tokenExpiresAt = nil
    }

    // MARK: - Keychain Operations

    private func save(_ value: String, forKey key: String) {
        guard let data = value.data(using: .utf8) else { return }

        // Delete existing item if any
        delete(forKey: key)

        // Create new item
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlock
        ]

        let status = SecItemAdd(query as CFDictionary, nil)

        if status != errSecSuccess {
            print("❌ Keychain save error for key \(key): \(status)")
        }
    }

    private func retrieveString(forKey key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess,
              let data = result as? Data,
              let string = String(data: data, encoding: .utf8) else {
            return nil
        }

        return string
    }

    private func delete(forKey key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: key
        ]

        SecItemDelete(query as CFDictionary)
    }

    // MARK: - Generic Storage (for other secure data)

    func save<T: Codable>(_ value: T, forKey key: String) {
        guard let data = try? JSONEncoder().encode(value),
              let string = String(data: data, encoding: .utf8) else {
            return
        }
        save(string, forKey: key)
    }

    func retrieve<T: Codable>(forKey key: String, as type: T.Type) -> T? {
        guard let string = retrieveString(forKey: key),
              let data = string.data(using: .utf8),
              let value = try? JSONDecoder().decode(T.self, from: data) else {
            return nil
        }
        return value
    }
}
