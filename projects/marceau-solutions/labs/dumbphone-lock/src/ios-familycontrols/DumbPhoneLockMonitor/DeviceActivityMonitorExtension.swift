import DeviceActivity
import ManagedSettings
import Foundation

/// Extension that monitors device activity and enforces app blocks
class DumbPhoneMonitor: DeviceActivityMonitor {
    
    let store = ManagedSettingsStore()
    
    override func intervalDidStart(for activity: DeviceActivityName) {
        super.intervalDidStart(for: activity)
        // Shields are already applied in the main app
        // This is called when the monitoring interval starts
    }
    
    override func intervalDidEnd(for activity: DeviceActivityName) {
        super.intervalDidEnd(for: activity)
        // Clear shields when interval ends
        store.shield.applications = nil
        store.shield.applicationCategories = nil
        store.shield.webDomains = nil
    }
    
    override func eventDidReachThreshold(_ event: DeviceActivityEvent.Name, activity: DeviceActivityName) {
        super.eventDidReachThreshold(event, activity: activity)
        // Can be used for time-based blocking
    }
}
