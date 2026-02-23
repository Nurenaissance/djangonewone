//
//  LoginView.swift
//  WhatsAppBusinessiOS
//
//  Modern iOS-native login screen
//

import SwiftUI

struct LoginView: View {
    @State private var viewModel = AuthViewModel()
    @State private var showRegister = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: Spacing.xl) {
                    // Logo and Title
                    HeaderSection()

                    // Login Form
                    LoginForm(viewModel: viewModel)

                    // Register Link
                    Button {
                        showRegister = true
                    } label: {
                        Text("Don't have an account? **Sign Up**")
                            .font(.body)
                            .foregroundColor(.textSecondary)
                    }
                    .padding(.top, Spacing.md)

                    Spacer()
                }
                .padding(Spacing.screenPadding)
            }
            .background(Color.backgroundPrimary)
            .navigationBarHidden(true)
            .alert("Error", isPresented: $viewModel.showError) {
                Button("OK") {
                    viewModel.dismissError()
                }
            } message: {
                if let error = viewModel.errorMessage {
                    Text(error)
                }
            }
            .sheet(isPresented: $showRegister) {
                RegisterView(viewModel: viewModel)
            }
        }
    }
}

// MARK: - Header Section

struct HeaderSection: View {
    var body: some View {
        VStack(spacing: Spacing.md) {
            // Logo
            ZStack {
                Circle()
                    .fill(Color.primary.gradient)
                    .frame(width: 100, height: 100)

                Image(systemName: "message.fill")
                    .font(.system(size: 50))
                    .foregroundColor(.white)
            }
            .padding(.top, Spacing.xxl)

            // Title
            Text("WhatsApp Business")
                .font(.largeTitle)
                .fontWeight(.bold)
                .foregroundColor(.textPrimary)

            // Subtitle
            Text("Sign in to manage your conversations")
                .font(.subheadline)
                .foregroundColor(.textSecondary)
                .multilineTextAlignment(.center)
        }
    }
}

// MARK: - Login Form

struct LoginForm: View {
    @Bindable var viewModel: AuthViewModel

    var body: some View {
        VStack(spacing: Spacing.lg) {
            // Username Field
            CustomTextField(
                title: "Username",
                text: $viewModel.username,
                icon: "person.fill",
                placeholder: "Enter your username"
            )
            .textContentType(.username)
            .textInputAutocapitalization(.never)
            .autocorrectionDisabled()

            // Password Field
            CustomSecureField(
                title: "Password",
                text: $viewModel.password,
                icon: "lock.fill",
                placeholder: "Enter your password"
            )
            .textContentType(.password)

            // Forgot Password
            HStack {
                Spacer()
                Button("Forgot Password?") {
                    // TODO: Implement forgot password
                }
                .font(.caption1)
                .foregroundColor(.primary)
            }

            // Login Button
            PrimaryButton(
                title: "Sign In",
                action: {
                    Task {
                        await viewModel.login()
                    }
                },
                isLoading: viewModel.isLoading,
                isDisabled: viewModel.username.isEmpty || viewModel.password.isEmpty,
                icon: "arrow.right"
            )
            .padding(.top, Spacing.md)
        }
        .padding(.top, Spacing.lg)
    }
}

// MARK: - Custom Text Field

struct CustomTextField: View {
    let title: String
    @Binding var text: String
    let icon: String
    let placeholder: String

    var body: some View {
        VStack(alignment: .leading, spacing: Spacing.xs) {
            Text(title)
                .font(.subheadline)
                .fontWeight(.medium)
                .foregroundColor(.textSecondary)

            HStack(spacing: Spacing.sm) {
                Image(systemName: icon)
                    .foregroundColor(.textTertiary)
                    .frame(width: 20)

                TextField(placeholder, text: $text)
                    .font(.input)
            }
            .padding(Spacing.md)
            .background(Color.backgroundSecondary)
            .cornerRadius(CornerRadius.input)
            .overlay(
                RoundedRectangle(cornerRadius: CornerRadius.input)
                    .stroke(Color.separator.opacity(0.5), lineWidth: 1)
            )
        }
    }
}

// MARK: - Custom Secure Field

struct CustomSecureField: View {
    let title: String
    @Binding var text: String
    let icon: String
    let placeholder: String

    @State private var isSecure = true

    var body: some View {
        VStack(alignment: .leading, spacing: Spacing.xs) {
            Text(title)
                .font(.subheadline)
                .fontWeight(.medium)
                .foregroundColor(.textSecondary)

            HStack(spacing: Spacing.sm) {
                Image(systemName: icon)
                    .foregroundColor(.textTertiary)
                    .frame(width: 20)

                if isSecure {
                    SecureField(placeholder, text: $text)
                        .font(.input)
                } else {
                    TextField(placeholder, text: $text)
                        .font(.input)
                }

                Button {
                    isSecure.toggle()
                } label: {
                    Image(systemName: isSecure ? "eye.slash.fill" : "eye.fill")
                        .foregroundColor(.textTertiary)
                }
            }
            .padding(Spacing.md)
            .background(Color.backgroundSecondary)
            .cornerRadius(CornerRadius.input)
            .overlay(
                RoundedRectangle(cornerRadius: CornerRadius.input)
                    .stroke(Color.separator.opacity(0.5), lineWidth: 1)
            )
        }
    }
}

// MARK: - Register View

struct RegisterView: View {
    @Bindable var viewModel: AuthViewModel
    @Environment(\.dismiss) var dismiss

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: Spacing.lg) {
                    // Username Field
                    CustomTextField(
                        title: "Username",
                        text: $viewModel.username,
                        icon: "person.fill",
                        placeholder: "Choose a username"
                    )
                    .textContentType(.username)
                    .textInputAutocapitalization(.never)

                    // Email Field
                    CustomTextField(
                        title: "Email",
                        text: $viewModel.email,
                        icon: "envelope.fill",
                        placeholder: "your@email.com"
                    )
                    .textContentType(.emailAddress)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.emailAddress)

                    // Password Field
                    CustomSecureField(
                        title: "Password",
                        text: $viewModel.password,
                        icon: "lock.fill",
                        placeholder: "Create a password"
                    )
                    .textContentType(.newPassword)

                    // Register Button
                    PrimaryButton(
                        title: "Create Account",
                        action: {
                            Task {
                                await viewModel.register()
                                if viewModel.isAuthenticated {
                                    dismiss()
                                }
                            }
                        },
                        isLoading: viewModel.isLoading,
                        isDisabled: viewModel.username.isEmpty ||
                                   viewModel.email.isEmpty ||
                                   viewModel.password.isEmpty
                    )
                    .padding(.top, Spacing.md)

                    // Terms
                    Text("By creating an account, you agree to our **Terms of Service** and **Privacy Policy**")
                        .font(.caption1)
                        .foregroundColor(.textSecondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                }
                .padding(Spacing.screenPadding)
            }
            .background(Color.backgroundPrimary)
            .navigationTitle("Create Account")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
            .alert("Error", isPresented: $viewModel.showError) {
                Button("OK") {
                    viewModel.dismissError()
                }
            } message: {
                if let error = viewModel.errorMessage {
                    Text(error)
                }
            }
        }
    }
}

// MARK: - Preview

#Preview("Login") {
    LoginView()
}

#Preview("Register") {
    RegisterView(viewModel: AuthViewModel())
}
