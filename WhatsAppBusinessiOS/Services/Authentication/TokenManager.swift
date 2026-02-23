//
//  TokenManager.swift
//  WhatsAppBusinessiOS
//
//  JWT token management with automatic refresh and deduplication
//

import Foundation

actor TokenManager {
    static let shared = TokenManager()

    private let secureStorage = SecureStorage.shared
    private var refreshTask: Task<String, Error>?

    // Refresh token 30 seconds before expiry
    private let refreshBuffer: TimeInterval = 30

    private init() {}

    // MARK: - Public API

    /// Get a valid access token (auto-refreshes if expired)
    func getValidToken() async throws -> String {
        // Check if we have a valid token
        if let token = secureStorage.accessToken,
           let expiresAt = secureStorage.tokenExpiresAt,
           Date().addingTimeInterval(refreshBuffer) < expiresAt {
            // Token is still valid
            return token
        }

        // Token expired or about to expire - refresh it
        return try await refreshToken()
    }

    /// Refresh the access token using the refresh token
    func refreshToken() async throws -> String {
        // Prevent concurrent refresh requests
        if let existingTask = refreshTask {
            return try await existingTask.value
        }

        let task = Task<String, Error> {
            defer { refreshTask = nil }

            guard let refreshToken = secureStorage.refreshToken else {
                throw AuthError.noRefreshToken
            }

            // Make refresh request
            let endpoint = Endpoint.refreshToken(refreshToken: refreshToken)

            // Direct URLSession call to avoid circular dependency with APIClient
            var request = try endpoint.asURLRequest()
            let (data, response) = try await URLSession.shared.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                throw NetworkError.invalidResponse
            }

            guard httpResponse.statusCode == 200...299 else {
                throw NetworkError.fromHTTPStatusCode(httpResponse.statusCode, data: data)
            }

            // Decode response
            let decoder = JSONDecoder()
            decoder.keyDecodingStrategy = .convertFromSnakeCase
            let tokenResponse = try decoder.decode(TokenResponse.self, from: data)

            // Save new tokens
            secureStorage.saveTokens(
                accessToken: tokenResponse.accessToken,
                refreshToken: tokenResponse.refreshToken,
                expiresIn: tokenResponse.expiresIn
            )

            // Save user info
            if let tenantId = tokenResponse.tenantId {
                UserDefaults.standard.tenantId = tenantId
            }
            if let userId = tokenResponse.userId {
                UserDefaults.standard.userId = userId
            }

            return tokenResponse.accessToken
        }

        refreshTask = task
        return try await task.value
    }

    /// Login with username and password
    func login(username: String, password: String) async throws -> TokenResponse {
        let endpoint = Endpoint.login(username: username, password: password)

        var request = try endpoint.asURLRequest()
        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }

        guard httpResponse.statusCode == 200...299 else {
            throw NetworkError.fromHTTPStatusCode(httpResponse.statusCode, data: data)
        }

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let tokenResponse = try decoder.decode(TokenResponse.self, from: data)

        // Save tokens
        secureStorage.saveTokens(
            accessToken: tokenResponse.accessToken,
            refreshToken: tokenResponse.refreshToken,
            expiresIn: tokenResponse.expiresIn
        )

        // Save user info
        if let tenantId = tokenResponse.tenantId {
            UserDefaults.standard.tenantId = tenantId
        }
        if let userId = tokenResponse.userId {
            UserDefaults.standard.userId = userId
        }

        return tokenResponse
    }

    /// Logout - clear all tokens and user data
    func logout() {
        secureStorage.clearTokens()
        UserDefaults.standard.tenantId = nil
        UserDefaults.standard.userId = nil
        refreshTask?.cancel()
        refreshTask = nil
    }

    /// Check if user is authenticated
    func isAuthenticated() -> Bool {
        return secureStorage.accessToken != nil && secureStorage.refreshToken != nil
    }
}

// MARK: - Token Response

struct TokenResponse: Decodable {
    let accessToken: String
    let refreshToken: String
    let expiresIn: Int
    let tokenType: String?
    let tenantId: String?
    let userId: String?
    let tier: String?
    let role: String?

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case expiresIn = "expires_in"
        case tokenType = "token_type"
        case tenantId = "tenant_id"
        case userId = "user_id"
        case tier
        case role
    }
}

// MARK: - Auth Errors

enum AuthError: LocalizedError {
    case noRefreshToken
    case invalidCredentials
    case tokenExpired

    var errorDescription: String? {
        switch self {
        case .noRefreshToken:
            return "No refresh token available. Please log in again."
        case .invalidCredentials:
            return "Invalid username or password."
        case .tokenExpired:
            return "Your session has expired. Please log in again."
        }
    }
}
