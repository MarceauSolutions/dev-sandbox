import SwiftUI
import FamilyControls
import DeviceActivity
import ManagedSettings

@main
struct DumbPhoneLockApp: App {
    @StateObject private var appBlocker = AppBlocker.shared
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(appBlocker)
        }
    }
}
