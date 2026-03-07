import ManagedSettings
import ManagedSettingsUI
import UIKit

/// Customizes the shield (block screen) shown when trying to open blocked apps
class DumbPhoneShieldConfiguration: ShieldConfigurationDataSource {
    
    override func configuration(shielding application: Application) -> ShieldConfiguration {
        return ShieldConfiguration(
            backgroundBlurStyle: .systemUltraThinMaterialDark,
            backgroundColor: UIColor.black,
            icon: UIImage(systemName: "lock.fill"),
            title: ShieldConfiguration.Label(
                text: "App Blocked",
                color: UIColor.systemOrange
            ),
            subtitle: ShieldConfiguration.Label(
                text: "Stay focused. You've got this. 💪",
                color: UIColor.lightGray
            ),
            primaryButtonLabel: ShieldConfiguration.Label(
                text: "Back to DumbPhone",
                color: UIColor.black
            ),
            primaryButtonBackgroundColor: UIColor.systemOrange,
            secondaryButtonLabel: nil
        )
    }
    
    override func configuration(shielding application: Application, in category: ActivityCategory) -> ShieldConfiguration {
        return configuration(shielding: application)
    }
    
    override func configuration(shielding webDomain: WebDomain) -> ShieldConfiguration {
        return ShieldConfiguration(
            backgroundBlurStyle: .systemUltraThinMaterialDark,
            backgroundColor: UIColor.black,
            icon: UIImage(systemName: "globe"),
            title: ShieldConfiguration.Label(
                text: "Site Blocked",
                color: UIColor.systemOrange
            ),
            subtitle: ShieldConfiguration.Label(
                text: "Focus time. This site is blocked.",
                color: UIColor.lightGray
            ),
            primaryButtonLabel: ShieldConfiguration.Label(
                text: "Go Back",
                color: UIColor.black
            ),
            primaryButtonBackgroundColor: UIColor.systemOrange,
            secondaryButtonLabel: nil
        )
    }
    
    override func configuration(shielding webDomain: WebDomain, in category: ActivityCategory) -> ShieldConfiguration {
        return configuration(shielding: webDomain)
    }
}
