//
//  NetworkError.swift
//  WhatsAppBusinessiOS
//
//  Core networking error types with user-friendly messages
//

import Foundation

enum NetworkError: LocalizedError {
    case invalidURL
    case invalidResponse
    case noData
    case decodingError(Error)
    case encodingError(Error)
    case clientError(Int, String?)
    case serverError(Int, String?)
    case unauthorized
    case forbidden
    case notFound
    case timeout
    case noInternetConnection
    case unknown(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid server response"
        case .noData:
            return "No data received from server"
        case .decodingError(let error):
            return "Failed to decode response: \(error.localizedDescription)"
        case .encodingError(let error):
            return "Failed to encode request: \(error.localizedDescription)"
        case .clientError(let code, let message):
            return message ?? "Client error (Code: \(code))"
        case .serverError(let code, let message):
            return message ?? "Server error (Code: \(code)). Please try again later."
        case .unauthorized:
            return "Your session has expired. Please log in again."
        case .forbidden:
            return "You don't have permission to perform this action."
        case .notFound:
            return "The requested resource was not found."
        case .timeout:
            return "Request timed out. Please check your connection."
        case .noInternetConnection:
            return "No internet connection. Please check your network settings."
        case .unknown(let error):
            return "An unexpected error occurred: \(error.localizedDescription)"
        }
    }

    var recoverySuggestion: String? {
        switch self {
        case .unauthorized:
            return "Log in again to continue"
        case .timeout, .noInternetConnection:
            return "Check your internet connection and try again"
        case .serverError:
            return "Try again in a few minutes"
        case .forbidden:
            return "Contact your administrator if you believe this is an error"
        default:
            return "Please try again"
        }
    }

    var isRetryable: Bool {
        switch self {
        case .timeout, .noInternetConnection, .serverError:
            return true
        default:
            return false
        }
    }
}

// MARK: - HTTP Status Code Helpers

extension NetworkError {
    static func fromHTTPStatusCode(_ statusCode: Int, data: Data? = nil) -> NetworkError {
        // Try to extract error message from response
        var message: String?
        if let data = data,
           let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
            message = json["message"] as? String ?? json["error"] as? String
        }

        switch statusCode {
        case 401:
            return .unauthorized
        case 403:
            return .forbidden
        case 404:
            return .notFound
        case 408:
            return .timeout
        case 400...499:
            return .clientError(statusCode, message)
        case 500...599:
            return .serverError(statusCode, message)
        default:
            return .invalidResponse
        }
    }
}
