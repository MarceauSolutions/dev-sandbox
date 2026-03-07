import SwiftUI
import FamilyControls

struct ContentView: View {
    @EnvironmentObject var appBlocker: AppBlocker
    @State private var showingAppPicker = false
    
    var body: some View {
        ZStack {
            // Background
            Color.black.ignoresSafeArea()
            
            VStack(spacing: 30) {
                // Header
                VStack(spacing: 8) {
                    Image(systemName: appBlocker.isLockActive ? "lock.fill" : "lock.open")
                        .font(.system(size: 60))
                        .foregroundColor(appBlocker.isLockActive ? .orange : .gray)
                    
                    Text("DumbPhone Lock")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                        .foregroundColor(.white)
                    
                    Text(appBlocker.isLockActive ? "Focus Mode Active" : "Ready to Focus")
                        .font(.subheadline)
                        .foregroundColor(.gray)
                }
                .padding(.top, 40)
                
                Spacer()
                
                if !appBlocker.isAuthorized {
                    // Authorization needed
                    AuthorizationView()
                } else if appBlocker.isLockActive {
                    // Lock is active - show status and unlock option
                    ActiveLockView()
                } else {
                    // Configure and start
                    ConfigurationView(showingAppPicker: $showingAppPicker)
                }
                
                Spacer()
                
                // Error message
                if let error = appBlocker.errorMessage {
                    Text(error)
                        .font(.caption)
                        .foregroundColor(.red)
                        .multilineTextAlignment(.center)
                        .padding()
                }
                
                // Footer
                Text("Embrace the Pain & Defy the Odds")
                    .font(.caption)
                    .foregroundColor(.gray.opacity(0.5))
                    .padding(.bottom, 20)
            }
        }
        .familyActivityPicker(isPresented: $showingAppPicker, selection: $appBlocker.selectedApps)
    }
}

// MARK: - Authorization View
struct AuthorizationView: View {
    @EnvironmentObject var appBlocker: AppBlocker
    
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "hand.raised.fill")
                .font(.system(size: 50))
                .foregroundColor(.orange)
            
            Text("Screen Time Access Required")
                .font(.headline)
                .foregroundColor(.white)
            
            Text("DumbPhone Lock needs Screen Time access to block distracting apps during your focus sessions.")
                .font(.subheadline)
                .foregroundColor(.gray)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 40)
            
            Button(action: {
                Task {
                    await appBlocker.requestAuthorization()
                }
            }) {
                Text("Enable Access")
                    .fontWeight(.semibold)
                    .foregroundColor(.black)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.orange)
                    .cornerRadius(12)
            }
            .padding(.horizontal, 40)
        }
    }
}

// MARK: - Configuration View
struct ConfigurationView: View {
    @EnvironmentObject var appBlocker: AppBlocker
    @Binding var showingAppPicker: Bool
    
    var body: some View {
        VStack(spacing: 25) {
            // App selection
            Button(action: { showingAppPicker = true }) {
                HStack {
                    Image(systemName: "app.badge")
                        .font(.title2)
                    
                    VStack(alignment: .leading) {
                        Text("Select Apps to Block")
                            .fontWeight(.medium)
                        
                        let count = appBlocker.selectedApps.applicationTokens.count + 
                                   appBlocker.selectedApps.categoryTokens.count
                        Text(count > 0 ? "\(count) selected" : "Tap to choose")
                            .font(.caption)
                            .foregroundColor(.gray)
                    }
                    
                    Spacer()
                    
                    Image(systemName: "chevron.right")
                        .foregroundColor(.gray)
                }
                .foregroundColor(.white)
                .padding()
                .background(Color.gray.opacity(0.2))
                .cornerRadius(12)
            }
            .padding(.horizontal, 30)
            
            // Duration picker
            VStack(alignment: .leading, spacing: 10) {
                Text("Focus Duration")
                    .font(.subheadline)
                    .foregroundColor(.gray)
                
                Picker("Duration", selection: $appBlocker.focusDurationMinutes) {
                    Text("15 min").tag(15)
                    Text("30 min").tag(30)
                    Text("1 hour").tag(60)
                    Text("2 hours").tag(120)
                    Text("Until I stop").tag(0)
                }
                .pickerStyle(.segmented)
                .colorMultiply(.orange)
            }
            .padding(.horizontal, 30)
            
            // Preset buttons
            HStack(spacing: 12) {
                ForEach(BlockingPreset.allCases, id: \.self) { preset in
                    Button(action: {
                        appBlocker.applyPreset(preset)
                        showingAppPicker = true
                    }) {
                        Text(preset.rawValue)
                            .font(.caption)
                            .foregroundColor(.orange)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(Color.orange.opacity(0.5), lineWidth: 1)
                            )
                    }
                }
            }
            
            // Start button
            Button(action: {
                appBlocker.startFocusLock()
            }) {
                HStack {
                    Image(systemName: "lock.fill")
                    Text("Start Focus Lock")
                        .fontWeight(.bold)
                }
                .foregroundColor(.black)
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.orange)
                .cornerRadius(12)
            }
            .padding(.horizontal, 30)
            .padding(.top, 10)
        }
    }
}

// MARK: - Active Lock View
struct ActiveLockView: View {
    @EnvironmentObject var appBlocker: AppBlocker
    @State private var showingUnlockConfirm = false
    
    var body: some View {
        VStack(spacing: 30) {
            // Animated lock icon
            Image(systemName: "lock.fill")
                .font(.system(size: 80))
                .foregroundColor(.orange)
                .symbolEffect(.pulse)
            
            VStack(spacing: 8) {
                Text("Apps Locked")
                    .font(.title)
                    .fontWeight(.bold)
                    .foregroundColor(.white)
                
                Text("Stay focused. You've got this.")
                    .foregroundColor(.gray)
            }
            
            // Stats
            let blockedCount = appBlocker.selectedApps.applicationTokens.count + 
                              appBlocker.selectedApps.categoryTokens.count
            HStack(spacing: 40) {
                VStack {
                    Text("\(blockedCount)")
                        .font(.title)
                        .fontWeight(.bold)
                        .foregroundColor(.orange)
                    Text("Apps Blocked")
                        .font(.caption)
                        .foregroundColor(.gray)
                }
            }
            
            // Emergency unlock (with friction)
            Button(action: {
                showingUnlockConfirm = true
            }) {
                Text("End Focus Session")
                    .font(.subheadline)
                    .foregroundColor(.gray)
                    .padding()
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                    )
            }
            .confirmationDialog(
                "Are you sure?",
                isPresented: $showingUnlockConfirm,
                titleVisibility: .visible
            ) {
                Button("Yes, end focus session", role: .destructive) {
                    appBlocker.stopFocusLock()
                }
                Button("Keep focusing", role: .cancel) {}
            } message: {
                Text("You'll be able to access all apps again. Consider staying focused a bit longer!")
            }
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(AppBlocker.shared)
}
