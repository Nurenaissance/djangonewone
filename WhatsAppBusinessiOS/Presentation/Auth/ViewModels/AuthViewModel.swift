//
//  AuthViewModel.swift
//  WhatsAppBusinessiOS
//
//  Authentication view model with login, register, and logout logic
//

import Foundation
import SwiftUI

@MainActor
@Observable
class AuthViewModel {
    // MARK: - Published Properties

    var username: String = ""
    var password: String = ""
    var email: String = ""

    var isLoading: Bool = false
    var errorMessage: String?
    var showError: Bool = false
    var isAuthenticated: Bool = false

    // MARK: - Dependencies

    private let tokenManager = TokenManager.shared
    private let apiClient = APIClient.shared

    // MARK: - Initialization

    init() {
        // Configure API client
        Task {
            await apiClient.configure(tokenManager: tokenManager)
        }

        // Check if already authenticated
        checkAuthenticationStatus()
    }

    // MARK: - Authentication Methods

    func login() async {
        guard validate() else { return }

        isLoading = true
        errorMessage = nil

        do {
            let response = try await tokenManager.login(
                username: username,
                password: password
            )

            // Successful login
            isAuthenticated = true
            print("✅ Login successful. Tenant: \(response.tenantId ?? "unknown")")

            // Clear fields
            clearFields()

        } catch let error as NetworkError {
            errorMessage = error.errorDescription
            showError = true
            print("❌ Login failed: \(error)")

        } catch {
            errorMessage = "An unexpected error occurred. Please try again."
            showError = true
            print("❌ Login failed: \(error)")
        }

        isLoading = false
    }

    func register() async {
        guard validateRegistration() else { return }

        isLoading = true
        errorMessage = nil

        do {
            let endpoint = Endpoint.register(
                username: username,
                email: email,
                password: password
            )

            struct RegisterResponse: Decodable {
                let message: String
                let userId: String?

                enum CodingKeys: String, CodingKey {
                    case message
                    case userId = "user_id"
                }
            }

            let response: RegisterResponse = try await apiClient.request(
                endpoint,
                responseType: RegisterResponse.self
            )

            print("✅ Registration successful: \(response.message)")

            // After successful registration, automatically log in
            await login()

        } catch let error as NetworkError {
            errorMessage = error.errorDescription
            showError = true
            print("❌ Registration failed: \(error)")

        } catch {
            errorMessage = "An unexpected error occurred. Please try again."
            showError = true
            print("❌ Registration failed: \(error)")
        }

        isLoading = false
    }

    func logout() {
        tokenManager.logout()
        isAuthenticated = false
        clearFields()
        print("✅ Logged out successfully")
    }

    // MARK: - Validation

    private func validate() -> Bool {
        if username.isEmpty {
            errorMessage = "Please enter your username"
            showError = true
            return false
        }

        if password.isEmpty {
            errorMessage = "Please enter your password"
            showError = true
            return false
        }

        if password.count < 6 {
            errorMessage = "Password must be at least 6 characters"
            showError = true
            return false
        }

        return true
    }

    private func validateRegistration() -> Bool {
        if username.isEmpty {
            errorMessage = "Please enter a username"
            showError = true
            return false
        }

        if email.isEmpty {
            errorMessage = "Please enter your email"
            showError = true
            return false
        }

        if !isValidEmail(email) {
            errorMessage = "Please enter a valid email address"
            showError = true
            return false
        }

        if password.isEmpty {
            errorMessage = "Please enter a password"
            showError = true
            return false
        }

        if password.count < 6 {
            errorMessage = "Password must be at least 6 characters"
            showError = true
            return false
        }

        return true
    }

    private func isValidEmail(_ email: String) -> Bool {
        let emailRegex = "[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,64}"
        let emailPredicate = NSPredicate(format: "SELF MATCHES %@", emailRegex)
        return emailPredicate.evaluate(with: email)
    }

    // MARK: - Helpers

    private func checkAuthenticationStatus() {
        isAuthenticated = tokenManager.isAuthenticated()
    }

    private func clearFields() {
        username = ""
        password = ""
        email = ""
    }

    func dismissError() {
        showError = false
        errorMessage = nil
    }
}
