import Foundation
import FamilyControls
import ManagedSettings
import DeviceActivity
import Combine

/// Main controller for blocking distracting apps during Focus sessions
@MainActor
class AppBlocker: ObservableObject {
    static let shared = AppBlocker()
    
    @Published var isAuthorized = false
    @Published var isLockActive = false
    @Published var selectedApps: FamilyActivitySelection = FamilyActivitySelection()
    @Published var focusDurationMinutes: Int = 30
    @Published var errorMessage: String?
    
    private let center = AuthorizationCenter.shared
    private let store = ManagedSettingsStore()
    private let deviceActivityCenter = DeviceActivityCenter()
    
    // Activity name for tracking
    private let focusActivityName = DeviceActivityName("dumbphone.focus")
    
    init() {
        // Check existing authorization
        Task {
            await checkAuthorization()
        }
    }
    
    /// Request Screen Time authorization
    func requestAuthorization() async {
        do {
            try await center.requestAuthorization(for: .individual)
            isAuthorized = true
            errorMessage = nil
        } catch {
            errorMessage = "Authorization failed: \(error.localizedDescription)"
            isAuthorized = false
        }
    }
    
    /// Check if already authorized
    func checkAuthorization() async {
        switch center.authorizationStatus {
        case .approved:
            isAuthorized = true
        case .denied, .notDetermined:
            isAuthorized = false
        @unknown default:
            isAuthorized = false
        }
    }
    
    /// Start blocking selected apps
    func startFocusLock() {
        guard isAuthorized else {
            errorMessage = "Not authorized. Please enable Screen Time access."
            return
        }
        
        guard !selectedApps.applicationTokens.isEmpty || !selectedApps.categoryTokens.isEmpty else {
            errorMessage = "No apps selected to block."
            return
        }
        
        // Block the selected apps
        store.shield.applications = selectedApps.applicationTokens
        store.shield.applicationCategories = .specific(selectedApps.categoryTokens)
        store.shield.webDomains = selectedApps.webDomainTokens
        
        // Schedule the activity monitoring
        let schedule = DeviceActivitySchedule(
            intervalStart: DateComponents(hour: 0, minute: 0),
            intervalEnd: DateComponents(hour: 23, minute: 59),
            repeats: false
        )
        
        do {
            try deviceActivityCenter.startMonitoring(focusActivityName, during: schedule)
            isLockActive = true
            errorMessage = nil
            
            // Haptic feedback
            let generator = UINotificationFeedbackGenerator()
            generator.notificationOccurred(.success)
        } catch {
            errorMessage = "Failed to start monitoring: \(error.localizedDescription)"
        }
    }
    
    /// Stop blocking apps (end focus session)
    func stopFocusLock() {
        // Remove all shields
        store.shield.applications = nil
        store.shield.applicationCategories = nil
        store.shield.webDomains = nil
        
        // Stop monitoring
        deviceActivityCenter.stopMonitoring([focusActivityName])
        
        isLockActive = false
        
        // Haptic feedback
        let generator = UINotificationFeedbackGenerator()
        generator.notificationOccurred(.warning)
    }
    
    /// Quick presets for common blocking scenarios
    func applyPreset(_ preset: BlockingPreset) {
        // Note: Presets work with category tokens
        // The actual selection happens in the FamilyActivityPicker
        switch preset {
        case .socialMedia:
            // User should select social media apps in the picker
            focusDurationMinutes = 30
        case .allEntertainment:
            // User should select entertainment category
            focusDurationMinutes = 60
        case .nuclear:
            // Block everything except essentials
            focusDurationMinutes = 120
        }
    }
}

enum BlockingPreset: String, CaseIterable {
    case socialMedia = "Social Media"
    case allEntertainment = "All Entertainment"  
    case nuclear = "Nuclear (Everything)"
}
