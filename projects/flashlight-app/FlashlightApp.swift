import SwiftUI
import AVFoundation

@main
struct FlashlightApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

struct ContentView: View {
    @State private var isOn = false
    @State private var brightness: Float = 1.0
    @State private var errorMessage: String?
    
    var body: some View {
        ZStack {
            // Background changes with flashlight state
            (isOn ? Color.yellow.opacity(0.3) : Color.black)
                .ignoresSafeArea()
            
            VStack(spacing: 40) {
                Spacer()
                
                // Main toggle button
                Button(action: toggleFlashlight) {
                    ZStack {
                        Circle()
                            .fill(isOn ? Color.yellow : Color.gray.opacity(0.3))
                            .frame(width: 200, height: 200)
                            .shadow(color: isOn ? .yellow : .clear, radius: 30)
                        
                        Image(systemName: isOn ? "flashlight.on.fill" : "flashlight.off.fill")
                            .font(.system(size: 80))
                            .foregroundColor(isOn ? .black : .white)
                    }
                }
                
                // Brightness slider (only when on)
                if isOn {
                    VStack {
                        Text("Brightness")
                            .foregroundColor(.white)
                            .font(.headline)
                        
                        Slider(value: $brightness, in: 0.1...1.0) { _ in
                            updateBrightness()
                        }
                        .accentColor(.yellow)
                        .padding(.horizontal, 50)
                    }
                    .transition(.opacity)
                }
                
                // Status text
                Text(isOn ? "ON" : "TAP TO TURN ON")
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(isOn ? .yellow : .gray)
                
                if let error = errorMessage {
                    Text(error)
                        .foregroundColor(.red)
                        .font(.caption)
                        .multilineTextAlignment(.center)
                        .padding()
                }
                
                Spacer()
                
                // Info text
                Text("Works during FaceTime! 📞🔦")
                    .font(.caption)
                    .foregroundColor(.gray)
                    .padding(.bottom, 30)
            }
        }
        .animation(.easeInOut(duration: 0.3), value: isOn)
    }
    
    func toggleFlashlight() {
        guard let device = AVCaptureDevice.default(for: .video) else {
            errorMessage = "No camera available"
            return
        }
        
        guard device.hasTorch else {
            errorMessage = "Device doesn't have a flashlight"
            return
        }
        
        do {
            try device.lockForConfiguration()
            
            if isOn {
                device.torchMode = .off
            } else {
                try device.setTorchModeOn(level: brightness)
            }
            
            device.unlockForConfiguration()
            isOn.toggle()
            errorMessage = nil
            
            // Haptic feedback
            let generator = UIImpactFeedbackGenerator(style: .medium)
            generator.impactOccurred()
            
        } catch {
            errorMessage = "Error: \(error.localizedDescription)"
        }
    }
    
    func updateBrightness() {
        guard isOn else { return }
        
        guard let device = AVCaptureDevice.default(for: .video),
              device.hasTorch else { return }
        
        do {
            try device.lockForConfiguration()
            try device.setTorchModeOn(level: brightness)
            device.unlockForConfiguration()
        } catch {
            errorMessage = "Couldn't adjust brightness"
        }
    }
}

#Preview {
    ContentView()
}
