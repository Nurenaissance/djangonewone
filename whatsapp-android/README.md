# WhatsApp Business Automation - Android App

Native Android application built with **Kotlin** and **Jetpack Compose** for WhatsApp Business Automation CRM platform.

## 📋 Project Details

- **Package Name:** `com.whatsapp.business.automation`
- **Min SDK:** 24 (Android 7.0)
- **Target SDK:** 34 (Android 14)
- **Language:** Kotlin 100%
- **UI Framework:** Jetpack Compose
- **Architecture:** Clean Architecture + MVVM
- **Dependency Injection:** Hilt

## 🚀 Getting Started

### Prerequisites

1. **Android Studio** (Latest stable version - Hedgehog or newer)
2. **JDK 17** or higher
3. **Firebase Account** (you mentioned you have an existing Firebase project)
4. **Google Play Developer Account** (you have this)

### Setup Instructions

#### Step 1: Open Project in Android Studio

1. Launch Android Studio
2. Click "Open" and navigate to:
   ```
   C:\Users\Adarsh\MyProject\Deployed_Finals\djangobackendaug2025\whatsapp_latest_final-mainjunk\whatsapp-android
   ```
3. Wait for Gradle sync to complete (this may take several minutes on first run)

#### Step 2: Configure Firebase

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your existing Firebase project
3. Click "Add app" → Select Android icon
4. Enter package name: `com.whatsapp.business.automation`
5. Download the `google-services.json` file
6. Place it in: `whatsapp-android/app/google-services.json`

**IMPORTANT:** The `google-services.json` file is required for the app to build successfully!

#### Step 3: Build the Project

1. In Android Studio, click **Build** → **Make Project** (or press Ctrl+F9)
2. Wait for build to complete
3. Fix any errors that appear (most likely missing `google-services.json`)

#### Step 4: Run the App

**Option A: Emulator**
1. Create an Android Virtual Device (AVD) in Android Studio
   - Tools → Device Manager → Create Device
   - Recommended: Pixel 5 with Android 13 (API 33)
2. Click the green "Run" button (or press Shift+F10)

**Option B: Physical Device**
1. Enable Developer Options on your Android device
2. Enable USB Debugging
3. Connect device via USB
4. Click "Run" and select your device

## 📂 Project Structure

```
app/src/main/
├── java/com/whatsapp/business/automation/
│   ├── WhatsAppApp.kt                    # Application class (Hilt setup)
│   ├── MainActivity.kt                   # Main activity
│   │
│   ├── di/                               # Dependency Injection (TO BE CREATED)
│   ├── data/                             # Data Layer (TO BE CREATED)
│   ├── domain/                           # Business Logic (TO BE CREATED)
│   ├── presentation/                     # UI Layer (TO BE CREATED)
│   └── utils/                            # Utilities (TO BE CREATED)
│
├── res/
│   ├── values/
│   │   ├── strings.xml                   # String resources ✅
│   │   ├── colors.xml                    # Color palette ✅
│   │   └── themes.xml                    # App theme ✅
│   └── xml/
│       ├── network_security_config.xml   # Network security ✅
│       ├── backup_rules.xml              # Backup config ✅
│       └── data_extraction_rules.xml     # Data extraction ✅
│
└── AndroidManifest.xml                   # App manifest ✅
```

## 🎯 Current Status

### ✅ Completed
- [x] Project structure created
- [x] Build.gradle configured with all dependencies
- [x] AndroidManifest with permissions
- [x] Resource files (strings, colors, themes)
- [x] Application class with notification channels
- [x] MainActivity with basic Compose setup
- [x] ProGuard rules
- [x] Network security configuration

### 🔄 In Progress
- [ ] Firebase setup (waiting for google-services.json)

### 📝 Next Steps (Week 1-2)
- [ ] Create network layer (Retrofit, OkHttp)
- [ ] Implement authentication (JWT, token management)
- [ ] Build login/register screens
- [ ] Setup Room database
- [ ] Create navigation graph
- [ ] Build dashboard screen

## 🏗️ Architecture

### Layers

1. **Presentation Layer** (UI)
   - Jetpack Compose screens
   - ViewModels with StateFlow
   - Navigation

2. **Domain Layer** (Business Logic)
   - Use cases
   - Domain models
   - Validators

3. **Data Layer** (Data Sources)
   - Repositories
   - Remote data sources (Retrofit)
   - Local data sources (Room)
   - DTOs and mappers

### Key Libraries

| Category | Library | Version |
|----------|---------|---------|
| UI | Jetpack Compose | BOM 2023.10.01 |
| DI | Hilt | 2.48 |
| Network | Retrofit | 2.9.0 |
| Database | Room | 2.6.1 |
| Async | Coroutines | 1.7.3 |
| Real-time | Socket.IO | 2.1.0 |
| Images | Coil | 2.5.0 |
| Charts | MPAndroidChart | 3.1.0 |
| Firebase | Firebase BOM | 32.6.0 |

## 🔗 Backend APIs

The app connects to these backend services:

1. **Django Backend**
   - URL: `https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/`
   - Purpose: Main CRM, auth, contacts, campaigns

2. **FastAPI Backend**
   - URL: `https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net/`
   - Purpose: Analytics, real-time operations

3. **Node.js Bot Server**
   - URL: `https://whatsappbotserver.azurewebsites.net/`
   - Purpose: WhatsApp integration, Socket.IO

## 🔐 Authentication

The app uses:
- JWT tokens from Django backend
- Service-to-service keys via `X-Service-Key` header
- Secure token storage with EncryptedSharedPreferences

## 📱 Features (Planned)

### MVP (6-8 weeks)

**Week 1-2: Foundation**
- ✅ Project setup
- ⏳ Authentication (login, register)
- ⏳ Dashboard with stats

**Week 3-4: Contacts & Messaging**
- Contact management (CRUD)
- Real-time chat (Socket.IO)
- WhatsApp integration
- Media support (images, videos, documents)

**Week 5-6: Campaigns**
- Message templates
- Campaign creation wizard
- Broadcast groups
- Push notifications (FCM)

**Week 7-8: Analytics & Polish**
- Analytics dashboard with charts
- Campaign performance metrics
- Settings & profile
- Dark mode
- Error handling & offline mode

## 🐛 Common Issues & Solutions

### Issue: Gradle Sync Failed
**Solution:** Ensure you have:
- JDK 17 installed
- Latest Android Studio
- Internet connection (for downloading dependencies)

### Issue: google-services.json missing
**Solution:** Download from Firebase Console and place in `app/` directory

### Issue: Build fails with "Hilt" errors
**Solution:**
1. Clean project: Build → Clean Project
2. Rebuild: Build → Rebuild Project

### Issue: App crashes on launch
**Solution:** Check Logcat in Android Studio for error details

## 📚 Resources

- [Jetpack Compose Documentation](https://developer.android.com/jetpack/compose)
- [Hilt Documentation](https://developer.android.com/training/dependency-injection/hilt-android)
- [Material Design 3](https://m3.material.io/)
- [Retrofit Documentation](https://square.github.io/retrofit/)
- [Room Documentation](https://developer.android.com/training/data-storage/room)

## 👨‍💻 Development Workflow

### Running Tests
```bash
# Unit tests
./gradlew test

# Instrumented tests (requires emulator/device)
./gradlew connectedAndroidTest
```

### Building APK
```bash
# Debug APK
./gradlew assembleDebug

# Release APK (requires signing key)
./gradlew assembleRelease
```

### Building AAB (for Play Store)
```bash
./gradlew bundleRelease
```

## 📄 License

Proprietary - WhatsApp Business Automation Platform

---

**Status:** 🚧 Under Active Development - Week 1 of 8

**Next Task:** Setup Firebase and create network layer with Retrofit
