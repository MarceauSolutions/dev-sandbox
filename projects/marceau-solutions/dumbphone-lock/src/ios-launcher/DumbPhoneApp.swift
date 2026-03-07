import SwiftUI
import CoreLocation
import WeatherKit
import UIKit

// MARK: - Brand Theme

struct Brand {
    static let gold = Color(red: 201/255, green: 150/255, blue: 60/255)
    static let charcoal = Color(red: 51/255, green: 51/255, blue: 51/255)
    static let darkBg = Color(red: 18/255, green: 18/255, blue: 18/255)
    static let cardBg = Color(red: 30/255, green: 30/255, blue: 30/255)
}

// MARK: - App Tile Model

struct AppTile: Identifiable, Codable, Equatable {
    var id: String { key }
    let key: String
    let name: String
    let icon: String
    let urlScheme: String
    let category: String
    static func == (lhs: AppTile, rhs: AppTile) -> Bool { lhs.key == rhs.key }
}

// MARK: - App Registry

struct AppRegistry {
    static let all: [AppTile] = [
        // Communication
        AppTile(key: "phone", name: "Phone", icon: "phone.fill", urlScheme: "mobilephone://", category: "Communication"),
        AppTile(key: "messages", name: "Messages", icon: "message.fill", urlScheme: "sms:", category: "Communication"),
        AppTile(key: "facetime", name: "FaceTime", icon: "video.fill", urlScheme: "facetime://", category: "Communication"),
        AppTile(key: "telegram", name: "Telegram", icon: "paperplane.fill", urlScheme: "tg://resolve", category: "Communication"),
        AppTile(key: "whatsapp", name: "WhatsApp", icon: "phone.bubble.fill", urlScheme: "whatsapp://", category: "Communication"),

        // Productivity
        AppTile(key: "gmail", name: "Gmail", icon: "envelope.fill", urlScheme: "googlegmail://", category: "Productivity"),
        AppTile(key: "gcal", name: "Calendar", icon: "calendar", urlScheme: "googlecalendar://", category: "Productivity"),
        AppTile(key: "notes", name: "Notes", icon: "note.text", urlScheme: "mobilenotes://", category: "Productivity"),

        // Utilities
        AppTile(key: "gmaps", name: "Maps", icon: "map.fill", urlScheme: "comgooglemaps://", category: "Utilities"),
        AppTile(key: "ddg", name: "Browser", icon: "globe", urlScheme: "ddgQuickLink://", category: "Utilities"),
        AppTile(key: "camera", name: "Camera", icon: "camera.fill", urlScheme: "camera://", category: "Utilities"),

        // AI
        AppTile(key: "claude", name: "Claude", icon: "brain.head.profile.fill", urlScheme: "claude://", category: "AI"),
        AppTile(key: "grok", name: "Grok", icon: "sparkles", urlScheme: "grok://", category: "AI"),
        AppTile(key: "chatgpt", name: "ChatGPT", icon: "bubble.left.and.text.bubble.right.fill", urlScheme: "chatgpt://", category: "AI"),

        // Business
        AppTile(key: "stripe", name: "Stripe", icon: "dollarsign.circle.fill", urlScheme: "stripe-dashboard://", category: "Business"),
        AppTile(key: "amex", name: "Amex", icon: "creditcard.fill", urlScheme: "amex://", category: "Business"),
        AppTile(key: "chase", name: "Chase", icon: "building.columns.fill", urlScheme: "chase://", category: "Business"),
        AppTile(key: "venmo", name: "Venmo", icon: "banknote.fill", urlScheme: "venmo://", category: "Business"),
        AppTile(key: "cashapp", name: "Cash App", icon: "dollarsign.square.fill", urlScheme: "cashme://", category: "Business"),

        // Security
        AppTile(key: "authy", name: "Authy", icon: "lock.shield.fill", urlScheme: "authy://", category: "Security"),
        AppTile(key: "gauth", name: "G Auth", icon: "key.fill", urlScheme: "otpauth://", category: "Security"),

        // Health
        AppTile(key: "health", name: "Health", icon: "heart.fill", urlScheme: "x-apple-health://", category: "Health"),
        AppTile(key: "fitness", name: "Fitness", icon: "figure.run", urlScheme: "trainerize://", category: "Health"),

        // System
        AppTile(key: "settings", name: "Settings", icon: "gear", urlScheme: "app-settings:", category: "System"),
        AppTile(key: "clock", name: "Clock", icon: "clock.fill", urlScheme: "clock-alarm://", category: "System"),
        AppTile(key: "flashlight", name: "Light", icon: "flashlight.on.fill", urlScheme: "com.marceausolutions.flashlight://", category: "System"),
    ]

    static func tile(for key: String) -> AppTile? {
        all.first { $0.key == key }
    }
}

// MARK: - Settings Manager

class SettingsManager: ObservableObject {
    @Published var enabledAppKeys: [String] { didSet { save() } }
    @Published var focusDuration: Int { didSet { UserDefaults.standard.set(focusDuration, forKey: "focusDuration") } }
    @Published var sessionActive: Bool = false
    @Published var sessionEndTime: Date?
    @Published var hasCompletedSetup: Bool { didSet { UserDefaults.standard.set(hasCompletedSetup, forKey: "setupComplete") } }
    @Published var grayscaleEnabled: Bool = false

    static let defaultApps = [
        "phone", "messages", "facetime", "gmail", "gcal", "gmaps",
        "ddg", "camera", "notes", "claude", "grok", "stripe",
        "authy", "telegram"
    ]

    init() {
        let setupDone = UserDefaults.standard.bool(forKey: "setupComplete")
        hasCompletedSetup = setupDone

        if let saved = UserDefaults.standard.array(forKey: "enabledApps") as? [String] {
            enabledAppKeys = saved
        } else {
            enabledAppKeys = Self.defaultApps
        }
        focusDuration = UserDefaults.standard.integer(forKey: "focusDuration")
        if focusDuration == 0 { focusDuration = 60 }

        if let endTime = UserDefaults.standard.object(forKey: "sessionEndTime") as? Date {
            if endTime > Date() {
                sessionActive = true
                sessionEndTime = endTime
            } else {
                UserDefaults.standard.removeObject(forKey: "sessionEndTime")
            }
        }
    }

    func save() { UserDefaults.standard.set(enabledAppKeys, forKey: "enabledApps") }

    var enabledApps: [AppTile] { enabledAppKeys.compactMap { AppRegistry.tile(for: $0) } }

    func startSession() {
        let end = Date().addingTimeInterval(Double(focusDuration) * 60)
        sessionEndTime = end
        sessionActive = true
        UserDefaults.standard.set(end, forKey: "sessionEndTime")
    }

    func endSession() {
        sessionActive = false
        sessionEndTime = nil
        UserDefaults.standard.removeObject(forKey: "sessionEndTime")
    }

    func isEnabled(_ key: String) -> Bool { enabledAppKeys.contains(key) }

    func toggle(_ key: String) {
        if enabledAppKeys.contains(key) {
            enabledAppKeys.removeAll { $0 == key }
        } else {
            enabledAppKeys.append(key)
        }
    }
}

// MARK: - Weather Manager

class WeatherManager: NSObject, ObservableObject, CLLocationManagerDelegate {
    @Published var temperature: String = "--"
    @Published var condition: String = ""
    @Published var icon: String = "cloud.fill"
    private let locationManager = CLLocationManager()

    override init() {
        super.init()
        locationManager.delegate = self
        locationManager.desiredAccuracy = kCLLocationAccuracyKilometer
        locationManager.requestWhenInUseAuthorization()
        locationManager.requestLocation()
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.first else { return }
        Task { await fetchWeather(for: location) }
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        temperature = "72°"; condition = "Naples, FL"; icon = "sun.max.fill"
    }

    @MainActor
    func fetchWeather(for location: CLLocation) async {
        do {
            let weather = try await WeatherService.shared.weather(for: location)
            let f = weather.currentWeather.temperature.converted(to: .fahrenheit)
            temperature = "\(Int(f.value))°"
            condition = weather.currentWeather.condition.description
            icon = mapIcon(weather.currentWeather.condition)
        } catch {
            temperature = "72°"; condition = "Naples, FL"; icon = "sun.max.fill"
        }
    }

    func mapIcon(_ c: WeatherCondition) -> String {
        switch c {
        case .clear, .hot: return "sun.max.fill"
        case .mostlyClear: return "sun.min.fill"
        case .partlyCloudy: return "cloud.sun.fill"
        case .mostlyCloudy, .cloudy: return "cloud.fill"
        case .rain, .heavyRain: return "cloud.rain.fill"
        case .drizzle: return "cloud.drizzle.fill"
        case .thunderstorms: return "cloud.bolt.rain.fill"
        case .snow, .heavySnow: return "cloud.snow.fill"
        case .windy, .breezy: return "wind"
        case .foggy, .haze: return "cloud.fog.fill"
        default: return "cloud.fill"
        }
    }
}

// MARK: - App Entry

@main
struct DumbPhoneApp: App {
    @StateObject private var settings = SettingsManager()

    var body: some Scene {
        WindowGroup {
            if settings.hasCompletedSetup {
                MainView()
                    .environmentObject(settings)
                    .preferredColorScheme(.dark)
            } else {
                SetupWizardView()
                    .environmentObject(settings)
                    .preferredColorScheme(.dark)
            }
        }
    }
}

// MARK: - Setup Wizard

struct SetupWizardView: View {
    @EnvironmentObject var settings: SettingsManager
    @State private var step = 0

    var body: some View {
        ZStack {
            Brand.darkBg.ignoresSafeArea()

            VStack(spacing: 0) {
                // Progress
                HStack(spacing: 6) {
                    ForEach(0..<5) { i in
                        RoundedRectangle(cornerRadius: 2)
                            .fill(i <= step ? Brand.gold : Brand.gold.opacity(0.2))
                            .frame(height: 3)
                    }
                }
                .padding(.horizontal, 30)
                .padding(.top, 20)

                Spacer()

                switch step {
                case 0: welcomeStep
                case 1: appSelectionStep
                case 2: focusModeStep
                case 3: automationStep
                case 4: completeStep
                default: completeStep
                }

                Spacer()

                // Navigation
                HStack {
                    if step > 0 {
                        Button(action: { withAnimation { step -= 1 } }) {
                            Text("Back")
                                .font(.system(size: 16, weight: .medium))
                                .foregroundColor(.gray)
                        }
                    }
                    Spacer()
                    Button(action: {
                        withAnimation {
                            if step < 4 {
                                step += 1
                            } else {
                                settings.hasCompletedSetup = true
                            }
                        }
                    }) {
                        HStack(spacing: 8) {
                            Text(step == 4 ? "Launch" : "Next")
                                .font(.system(size: 16, weight: .semibold))
                            Image(systemName: step == 4 ? "arrow.right.circle.fill" : "chevron.right")
                        }
                        .foregroundColor(.black)
                        .padding(.horizontal, 28)
                        .padding(.vertical, 14)
                        .background(Brand.gold)
                        .cornerRadius(25)
                    }
                }
                .padding(.horizontal, 30)
                .padding(.bottom, 40)
            }
        }
    }

    var welcomeStep: some View {
        VStack(spacing: 20) {
            Image(systemName: "iphone.gen3")
                .font(.system(size: 60))
                .foregroundColor(Brand.gold)

            Text("Dumb Phone")
                .font(.system(size: 36, weight: .bold, design: .rounded))
                .foregroundColor(.white)

            Text("Turn your iPhone into a focused,\ndistraction-free tool.")
                .font(.system(size: 17, weight: .light))
                .foregroundColor(.gray)
                .multilineTextAlignment(.center)

            VStack(alignment: .leading, spacing: 12) {
                featureRow(icon: "apps.iphone", text: "Custom minimal launcher")
                featureRow(icon: "clock.fill", text: "Timed focus sessions")
                featureRow(icon: "paintbrush.fill", text: "Your brand, your colors")
                featureRow(icon: "gearshape.fill", text: "Add or remove apps anytime")
            }
            .padding(.top, 20)
        }
        .padding(.horizontal, 30)
    }

    var appSelectionStep: some View {
        VStack(spacing: 16) {
            Image(systemName: "square.grid.3x3.fill")
                .font(.system(size: 40))
                .foregroundColor(Brand.gold)

            Text("Choose Your Apps")
                .font(.system(size: 28, weight: .bold, design: .rounded))
                .foregroundColor(.white)

            Text("Select which apps appear on your launcher.\nYou can change these anytime in settings.")
                .font(.system(size: 15, weight: .light))
                .foregroundColor(.gray)
                .multilineTextAlignment(.center)

            ScrollView(showsIndicators: false) {
                LazyVGrid(columns: [
                    GridItem(.flexible()), GridItem(.flexible()),
                    GridItem(.flexible()), GridItem(.flexible())
                ], spacing: 14) {
                    ForEach(AppRegistry.all) { app in
                        Button(action: { settings.toggle(app.key) }) {
                            VStack(spacing: 6) {
                                ZStack {
                                    RoundedRectangle(cornerRadius: 16)
                                        .fill(settings.isEnabled(app.key) ? Brand.gold.opacity(0.15) : Brand.cardBg)
                                        .frame(width: 56, height: 56)
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 16)
                                                .stroke(settings.isEnabled(app.key) ? Brand.gold : Color.clear, lineWidth: 1.5)
                                        )
                                    Image(systemName: app.icon)
                                        .font(.system(size: 22))
                                        .foregroundColor(settings.isEnabled(app.key) ? Brand.gold : .gray)
                                }
                                Text(app.name)
                                    .font(.system(size: 10, weight: .medium))
                                    .foregroundColor(settings.isEnabled(app.key) ? .white : .gray)
                                    .lineLimit(1)
                            }
                        }
                    }
                }
                .padding(.horizontal, 10)
            }
        }
        .padding(.horizontal, 20)
    }

    var focusModeStep: some View {
        VStack(spacing: 20) {
            Image(systemName: "moon.fill")
                .font(.system(size: 40))
                .foregroundColor(Brand.gold)

            Text("Focus Mode Setup")
                .font(.system(size: 28, weight: .bold, design: .rounded))
                .foregroundColor(.white)

            Text("This hides other apps and blocks distracting\nnotifications when Dumb Phone mode is active.")
                .font(.system(size: 15, weight: .light))
                .foregroundColor(.gray)
                .multilineTextAlignment(.center)

            VStack(alignment: .leading, spacing: 16) {
                setupStep(number: "1", title: "Create Focus Mode", detail: "Settings → Focus → + → Custom → name it \"Dumb Phone\"", action: nil, handler: nil)

                setupStep(number: "2", title: "Set Allowed Apps", detail: "Inside Dumb Phone focus → Choose Apps → select only your essentials", action: nil, handler: nil)

                setupStep(number: "3", title: "Customize Home Screen", detail: "Inside Dumb Phone focus → Customize Screens → choose minimal page", action: nil, handler: nil)

                setupStep(number: "4", title: "Enable Grayscale", detail: "Settings → Accessibility → Display & Text Size → Color Filters → Grayscale", action: nil, handler: nil)
            }
            .padding(.top, 8)
        }
        .padding(.horizontal, 30)
    }

    var automationStep: some View {
        VStack(spacing: 20) {
            Image(systemName: "hand.tap.fill")
                .font(.system(size: 40))
                .foregroundColor(Brand.gold)

            Text("One-Tap Activation")
                .font(.system(size: 28, weight: .bold, design: .rounded))
                .foregroundColor(.white)

            Text("Double-tap the back of your phone\nto toggle Dumb Phone mode.")
                .font(.system(size: 15, weight: .light))
                .foregroundColor(.gray)
                .multilineTextAlignment(.center)

            VStack(alignment: .leading, spacing: 16) {
                setupStep(number: "1", title: "Create Shortcut", detail: "Open Shortcuts → + → Add 'Set Focus' (toggle Dumb Phone) + 'Set Color Filters' (toggle)", action: "Open Shortcuts") {
                    openURL("shortcuts://create-shortcut")
                }

                setupStep(number: "2", title: "Auto-Open Launcher", detail: "Shortcuts → Automation → + → Focus → Dumb Phone → Open App → DumbPhone", action: "Open Automations") {
                    openURL("shortcuts://create-automation")
                }

                setupStep(number: "3", title: "Assign Back Tap", detail: "Settings → Accessibility → Touch → Back Tap → Double Tap → Your Shortcut", action: nil, handler: nil)
            }
            .padding(.top, 8)
        }
        .padding(.horizontal, 30)
    }

    var completeStep: some View {
        VStack(spacing: 20) {
            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 60))
                .foregroundColor(Brand.gold)

            Text("You're Set")
                .font(.system(size: 36, weight: .bold, design: .rounded))
                .foregroundColor(.white)

            Text("Double-tap the back of your phone\nto enter Dumb Phone mode.\n\nTap the slider icon to customize\nyour apps anytime.")
                .font(.system(size: 17, weight: .light))
                .foregroundColor(.gray)
                .multilineTextAlignment(.center)

            VStack(spacing: 8) {
                Text("Focus Duration")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.white.opacity(0.6))
                HStack(spacing: 12) {
                    ForEach([30, 60, 90, 120], id: \.self) { mins in
                        Button(action: { settings.focusDuration = mins }) {
                            Text("\(mins)m")
                                .font(.system(size: 15, weight: .semibold, design: .rounded))
                                .foregroundColor(settings.focusDuration == mins ? .black : Brand.gold)
                                .padding(.horizontal, 18)
                                .padding(.vertical, 10)
                                .background(settings.focusDuration == mins ? Brand.gold : Brand.gold.opacity(0.1))
                                .cornerRadius(20)
                        }
                    }
                }
            }
            .padding(.top, 16)
        }
        .padding(.horizontal, 30)
    }

    func featureRow(icon: String, text: String) -> some View {
        HStack(spacing: 14) {
            Image(systemName: icon)
                .font(.system(size: 20))
                .foregroundColor(Brand.gold)
                .frame(width: 30)
            Text(text)
                .font(.system(size: 16, weight: .light))
                .foregroundColor(.white.opacity(0.8))
        }
    }

    func setupStep(number: String, title: String, detail: String, action: String?, handler: (() -> Void)?) -> some View {
        HStack(alignment: .top, spacing: 14) {
            Text(number)
                .font(.system(size: 14, weight: .bold, design: .rounded))
                .foregroundColor(.black)
                .frame(width: 28, height: 28)
                .background(Brand.gold)
                .cornerRadius(14)

            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.white)
                Text(detail)
                    .font(.system(size: 13, weight: .light))
                    .foregroundColor(.gray)

                if let actionText = action, let handler = handler {
                    Button(action: handler) {
                        Text(actionText)
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundColor(Brand.gold)
                    }
                    .padding(.top, 2)
                }
            }
        }
    }

    func openURL(_ string: String) {
        guard let url = URL(string: string) else { return }
        UIApplication.shared.open(url)
    }
}

// MARK: - Main View

struct MainView: View {
    @EnvironmentObject var settings: SettingsManager
    @State private var showSettings = false

    var body: some View {
        ZStack {
            LauncherView(showSettings: $showSettings)
            if showSettings {
                SettingsView(showSettings: $showSettings)
                    .transition(.move(edge: .trailing))
            }
        }
        .animation(.easeInOut(duration: 0.3), value: showSettings)
    }
}

// MARK: - Launcher View

struct LauncherView: View {
    @EnvironmentObject var settings: SettingsManager
    @StateObject private var weather = WeatherManager()
    @State private var currentTime = Date()
    @Binding var showSettings: Bool
    let timer = Timer.publish(every: 1, on: .main, in: .common).autoconnect()

    var timeString: String {
        let f = DateFormatter(); f.dateFormat = "h:mm"; return f.string(from: currentTime)
    }
    var amPm: String {
        let f = DateFormatter(); f.dateFormat = "a"; return f.string(from: currentTime)
    }
    var dateString: String {
        let f = DateFormatter(); f.dateFormat = "EEEE, MMMM d"; return f.string(from: currentTime)
    }

    var remainingTime: String? {
        guard settings.sessionActive, let end = settings.sessionEndTime else { return nil }
        let remaining = end.timeIntervalSince(currentTime)
        if remaining <= 0 {
            DispatchQueue.main.async { settings.endSession() }
            return nil
        }
        let h = Int(remaining) / 3600
        let m = (Int(remaining) % 3600) / 60
        return h > 0 ? "\(h)h \(m)m remaining" : "\(m)m remaining"
    }

    var body: some View {
        ZStack {
            Brand.darkBg.ignoresSafeArea()

            VStack(spacing: 0) {
                // Header
                HStack {
                    Spacer()
                    Button(action: { showSettings = true }) {
                        Image(systemName: "slider.horizontal.3")
                            .font(.system(size: 20))
                            .foregroundColor(Brand.gold.opacity(0.6))
                    }
                }
                .padding(.horizontal, 24)
                .padding(.top, 12)

                // Clock & Weather
                VStack(spacing: 6) {
                    HStack(alignment: .firstTextBaseline, spacing: 4) {
                        Text(timeString)
                            .font(.system(size: 60, weight: .ultraLight, design: .rounded))
                            .foregroundColor(.white)
                        Text(amPm)
                            .font(.system(size: 22, weight: .light, design: .rounded))
                            .foregroundColor(Brand.gold.opacity(0.6))
                    }
                    Text(dateString)
                        .font(.system(size: 16, weight: .light, design: .rounded))
                        .foregroundColor(.white.opacity(0.5))
                    HStack(spacing: 8) {
                        Image(systemName: weather.icon)
                            .font(.system(size: 18))
                            .foregroundColor(Brand.gold)
                        Text(weather.temperature)
                            .font(.system(size: 18, weight: .medium, design: .rounded))
                            .foregroundColor(.white)
                        Text(weather.condition)
                            .font(.system(size: 14, weight: .light))
                            .foregroundColor(.white.opacity(0.4))
                    }
                    .padding(.top, 2)

                    if let remaining = remainingTime {
                        HStack(spacing: 6) {
                            Image(systemName: "lock.fill").font(.system(size: 12))
                            Text(remaining).font(.system(size: 13, weight: .medium, design: .rounded))
                        }
                        .foregroundColor(Brand.gold)
                        .padding(.horizontal, 16).padding(.vertical, 6)
                        .background(Brand.gold.opacity(0.12))
                        .cornerRadius(20)
                        .padding(.top, 8)
                    }
                }
                .padding(.top, 8).padding(.bottom, 24)

                // App Grid
                ScrollView(showsIndicators: false) {
                    LazyVGrid(columns: [
                        GridItem(.flexible(), spacing: 12), GridItem(.flexible(), spacing: 12),
                        GridItem(.flexible(), spacing: 12), GridItem(.flexible(), spacing: 12)
                    ], spacing: 16) {
                        ForEach(settings.enabledApps) { app in
                            AppTileView(app: app)
                        }
                    }
                    .padding(.horizontal, 20)
                }

                Spacer()

                // Bottom
                Rectangle()
                    .fill(LinearGradient(
                        colors: [Brand.gold.opacity(0), Brand.gold.opacity(0.4), Brand.gold.opacity(0)],
                        startPoint: .leading, endPoint: .trailing
                    ))
                    .frame(height: 1)
                    .padding(.horizontal, 40)

                if !settings.sessionActive {
                    Button(action: { settings.startSession() }) {
                        HStack(spacing: 8) {
                            Image(systemName: "lock.fill").font(.system(size: 14))
                            Text("Start Focus (\(settings.focusDuration)m)")
                                .font(.system(size: 14, weight: .medium, design: .rounded))
                        }
                        .foregroundColor(Brand.gold)
                        .padding(.horizontal, 24).padding(.vertical, 10)
                        .background(Brand.gold.opacity(0.1))
                        .cornerRadius(25)
                        .overlay(RoundedRectangle(cornerRadius: 25).stroke(Brand.gold.opacity(0.3), lineWidth: 1))
                    }
                    .padding(.top, 12)
                }

                Text("Embrace the Pain & Defy the Odds")
                    .font(.system(size: 11, weight: .light, design: .rounded))
                    .foregroundColor(Brand.gold.opacity(0.3))
                    .padding(.top, 8).padding(.bottom, 24)
            }
        }
        .onReceive(timer) { currentTime = $0 }
    }
}

// MARK: - App Tile View

struct AppTileView: View {
    let app: AppTile

    var body: some View {
        Button(action: { openApp(app.urlScheme) }) {
            VStack(spacing: 8) {
                ZStack {
                    RoundedRectangle(cornerRadius: 18)
                        .fill(Brand.cardBg)
                        .frame(width: 64, height: 64)
                        .overlay(RoundedRectangle(cornerRadius: 18).stroke(Brand.gold.opacity(0.15), lineWidth: 1))
                    Image(systemName: app.icon)
                        .font(.system(size: 26))
                        .foregroundColor(Brand.gold)
                }
                Text(app.name)
                    .font(.system(size: 11, weight: .medium, design: .rounded))
                    .foregroundColor(.white.opacity(0.7))
                    .lineLimit(1)
            }
        }
    }

    func openApp(_ scheme: String) {
        // Try primary scheme
        if let url = URL(string: scheme), UIApplication.shared.canOpenURL(url) {
            UIApplication.shared.open(url)
            return
        }
        // Try without double slash
        let alt = scheme.replacingOccurrences(of: "://", with: ":")
        if let url = URL(string: alt), UIApplication.shared.canOpenURL(url) {
            UIApplication.shared.open(url)
            return
        }
        // Try just the scheme root
        let root = scheme.components(separatedBy: "://").first ?? scheme
        if let url = URL(string: root + "://") {
            UIApplication.shared.open(url)
        }
    }
}

// MARK: - Settings View

struct SettingsView: View {
    @EnvironmentObject var settings: SettingsManager
    @Binding var showSettings: Bool
    let categories = ["Communication", "Productivity", "Utilities", "AI", "Business", "Security", "Health", "System"]

    var body: some View {
        ZStack {
            Brand.darkBg.ignoresSafeArea()

            VStack(spacing: 0) {
                HStack {
                    Button(action: { showSettings = false }) {
                        HStack(spacing: 6) {
                            Image(systemName: "chevron.left")
                            Text("Back")
                        }
                        .font(.system(size: 16, weight: .medium))
                        .foregroundColor(Brand.gold)
                    }
                    Spacer()
                    Text("Configure")
                        .font(.system(size: 18, weight: .semibold, design: .rounded))
                        .foregroundColor(.white)
                    Spacer()
                    Button(action: {
                        settings.hasCompletedSetup = false
                    }) {
                        Image(systemName: "arrow.counterclockwise")
                            .font(.system(size: 16))
                            .foregroundColor(Brand.gold.opacity(0.5))
                    }
                }
                .padding(.horizontal, 20).padding(.top, 16).padding(.bottom, 20)

                // Duration
                VStack(alignment: .leading, spacing: 12) {
                    Text("FOCUS SESSION")
                        .font(.system(size: 12, weight: .semibold, design: .rounded))
                        .foregroundColor(Brand.gold.opacity(0.6))

                    HStack {
                        Text("Duration").foregroundColor(.white)
                        Spacer()
                        HStack(spacing: 12) {
                            ForEach([30, 60, 90, 120], id: \.self) { mins in
                                Button(action: { settings.focusDuration = mins }) {
                                    Text("\(mins)m")
                                        .font(.system(size: 14, weight: .medium, design: .rounded))
                                        .foregroundColor(settings.focusDuration == mins ? .black : Brand.gold)
                                        .padding(.horizontal, 12).padding(.vertical, 6)
                                        .background(settings.focusDuration == mins ? Brand.gold : Brand.gold.opacity(0.1))
                                        .cornerRadius(15)
                                }
                            }
                        }
                    }

                    if settings.sessionActive {
                        Button(action: { settings.endSession() }) {
                            HStack {
                                Image(systemName: "lock.open.fill")
                                Text("End Current Session")
                            }
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(.red)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 10)
                            .background(Color.red.opacity(0.1))
                            .cornerRadius(12)
                        }
                    }
                }
                .padding(.horizontal, 20).padding(.bottom, 24)

                // Apps
                ScrollView(showsIndicators: false) {
                    VStack(alignment: .leading, spacing: 20) {
                        ForEach(categories, id: \.self) { cat in
                            let apps = AppRegistry.all.filter { $0.category == cat }
                            if !apps.isEmpty {
                                VStack(alignment: .leading, spacing: 10) {
                                    Text(cat.uppercased())
                                        .font(.system(size: 12, weight: .semibold, design: .rounded))
                                        .foregroundColor(Brand.gold.opacity(0.6))
                                    ForEach(apps) { app in
                                        Button(action: { settings.toggle(app.key) }) {
                                            HStack(spacing: 14) {
                                                ZStack {
                                                    RoundedRectangle(cornerRadius: 12)
                                                        .fill(settings.isEnabled(app.key) ? Brand.gold.opacity(0.15) : Brand.cardBg)
                                                        .frame(width: 44, height: 44)
                                                    Image(systemName: app.icon)
                                                        .font(.system(size: 20))
                                                        .foregroundColor(settings.isEnabled(app.key) ? Brand.gold : .gray)
                                                }
                                                Text(app.name)
                                                    .font(.system(size: 16, weight: .medium, design: .rounded))
                                                    .foregroundColor(.white)
                                                Spacer()
                                                Image(systemName: settings.isEnabled(app.key) ? "checkmark.circle.fill" : "circle")
                                                    .font(.system(size: 22))
                                                    .foregroundColor(settings.isEnabled(app.key) ? Brand.gold : .gray.opacity(0.4))
                                            }
                                            .padding(.vertical, 4)
                                        }
                                    }
                                }
                            }
                        }
                    }
                    .padding(.horizontal, 20).padding(.bottom, 40)
                }
            }
        }
    }
}

#Preview {
    MainView().environmentObject(SettingsManager())
}
