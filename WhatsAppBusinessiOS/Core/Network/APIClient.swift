//
//  APIClient.swift
//  WhatsAppBusinessiOS
//
//  Core API client with automatic token refresh, multi-tenant support, and error handling
//

import Foundation

actor APIClient {
    static let shared = APIClient()

    private let session: URLSession
    private var tokenManager: TokenManager?

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.waitsForConnectivity = true
        config.requestCachePolicy = .reloadIgnoringLocalCacheData
        self.session = URLSession(configuration: config)
    }

    // MARK: - Setup

    func configure(tokenManager: TokenManager) {
        self.tokenManager = tokenManager
    }

    // MARK: - Request Methods

    /// Generic request method with automatic token refresh and error handling
    func request<T: Decodable>(
        _ endpoint: Endpoint,
        responseType: T.Type
    ) async throws -> T {
        var request = try endpoint.asURLRequest()

        // Add authentication header if required
        if endpoint.requiresAuth {
            guard let tokenManager = tokenManager else {
                throw NetworkError.unauthorized
            }
            let token = try await tokenManager.getValidToken()
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        // Add multi-tenant header
        if let tenantId = UserDefaults.standard.string(forKey: "tenant_id") {
            request.setValue(tenantId, forHTTPHeaderField: "X-Tenant-ID")
        }

        // Log request (debug mode)
        #if DEBUG
        print("🌐 API Request: \(request.httpMethod ?? "GET") \(request.url?.absoluteString ?? "")")
        if let body = request.httpBody, let bodyString = String(data: body, encoding: .utf8) {
            print("📦 Body: \(bodyString)")
        }
        #endif

        // Perform request
        do {
            let (data, response) = try await session.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                throw NetworkError.invalidResponse
            }

            #if DEBUG
            print("📡 Response: \(httpResponse.statusCode)")
            if let responseString = String(data: data, encoding: .utf8) {
                print("📥 Data: \(responseString)")
            }
            #endif

            // Handle different status codes
            switch httpResponse.statusCode {
            case 200...299:
                // Success - decode response
                do {
                    let decoder = JSONDecoder()
                    decoder.dateDecodingStrategy = .iso8601
                    return try decoder.decode(T.self, from: data)
                } catch {
                    throw NetworkError.decodingError(error)
                }

            case 401:
                // Unauthorized - try to refresh token
                if endpoint.requiresAuth, let tokenManager = tokenManager {
                    do {
                        // Attempt token refresh
                        try await tokenManager.refreshToken()
                        // Retry request with new token
                        return try await self.request(endpoint, responseType: responseType)
                    } catch {
                        // Refresh failed - user needs to re-login
                        throw NetworkError.unauthorized
                    }
                } else {
                    throw NetworkError.unauthorized
                }

            default:
                throw NetworkError.fromHTTPStatusCode(httpResponse.statusCode, data: data)
            }

        } catch let error as NetworkError {
            throw error
        } catch let error as URLError {
            // Handle URLError cases
            switch error.code {
            case .notConnectedToInternet, .networkConnectionLost:
                throw NetworkError.noInternetConnection
            case .timedOut:
                throw NetworkError.timeout
            default:
                throw NetworkError.unknown(error)
            }
        } catch {
            throw NetworkError.unknown(error)
        }
    }

    /// Request method for empty responses (e.g., DELETE)
    func requestEmpty(_ endpoint: Endpoint) async throws {
        struct EmptyResponse: Decodable {}
        _ = try await request(endpoint, responseType: EmptyResponse.self)
    }

    /// Upload multipart form data (for media uploads)
    func upload(
        _ endpoint: Endpoint,
        data: Data,
        filename: String,
        mimeType: String
    ) async throws -> MediaUploadResponse {
        var request = try endpoint.asURLRequest()

        // Generate boundary
        let boundary = UUID().uuidString

        // Add authentication
        if endpoint.requiresAuth {
            guard let tokenManager = tokenManager else {
                throw NetworkError.unauthorized
            }
            let token = try await tokenManager.getValidToken()
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        // Add tenant ID
        if let tenantId = UserDefaults.standard.string(forKey: "tenant_id") {
            request.setValue(tenantId, forHTTPHeaderField: "X-Tenant-ID")
        }

        // Set content type for multipart
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        // Create multipart body
        var body = Data()

        // Add file data
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: \(mimeType)\r\n\r\n".data(using: .utf8)!)
        body.append(data)
        body.append("\r\n".data(using: .utf8)!)
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        // Perform upload
        let (responseData, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }

        guard httpResponse.statusCode == 200...299 else {
            throw NetworkError.fromHTTPStatusCode(httpResponse.statusCode, data: responseData)
        }

        let decoder = JSONDecoder()
        return try decoder.decode(MediaUploadResponse.self, from: responseData)
    }

    /// Download data (for images, videos, etc.)
    func download(from url: URL) async throws -> Data {
        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200...299 else {
            throw NetworkError.invalidResponse
        }

        return data
    }
}

// MARK: - Response Types

struct MediaUploadResponse: Decodable {
    let url: String
    let filename: String
    let size: Int
}

struct EmptyResponse: Decodable {}

// MARK: - UserDefaults Extension

extension UserDefaults {
    var tenantId: String? {
        get { string(forKey: "tenant_id") }
        set { set(newValue, forKey: "tenant_id") }
    }

    var userId: String? {
        get { string(forKey: "user_id") }
        set { set(newValue, forKey: "user_id") }
    }
}
