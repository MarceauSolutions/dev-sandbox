#!/bin/bash
# Quick setup script for FaceTime Flashlight app
# Run this on your Mac, then open the project in Xcode

set -e

APP_NAME="Flashlight"
BUNDLE_ID="com.marceausolutions.flashlight"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🔦 Setting up FaceTime Flashlight app..."

# Create Xcode project directory
mkdir -p ~/Desktop/$APP_NAME/$APP_NAME

# Copy Swift file
cp "$SCRIPT_DIR/FlashlightApp.swift" ~/Desktop/$APP_NAME/$APP_NAME/

# Create the Xcode project file structure
mkdir -p ~/Desktop/$APP_NAME/$APP_NAME.xcodeproj

# Create project.pbxproj
cat > ~/Desktop/$APP_NAME/$APP_NAME.xcodeproj/project.pbxproj << 'PBXPROJ'
// !$*UTF8*$!
{
	archiveVersion = 1;
	classes = {
	};
	objectVersion = 56;
	objects = {

/* Begin PBXBuildFile section */
		A1000001 /* FlashlightApp.swift in Sources */ = {isa = PBXBuildFile; fileRef = A1000002; };
/* End PBXBuildFile section */

/* Begin PBXFileReference section */
		A1000002 /* FlashlightApp.swift */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = FlashlightApp.swift; sourceTree = "<group>"; };
		A1000003 /* Flashlight.app */ = {isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = Flashlight.app; sourceTree = BUILT_PRODUCTS_DIR; };
/* End PBXFileReference section */

/* Begin PBXGroup section */
		A1000010 = {
			isa = PBXGroup;
			children = (
				A1000011,
				A1000012,
			);
			sourceTree = "<group>";
		};
		A1000011 /* Flashlight */ = {
			isa = PBXGroup;
			children = (
				A1000002,
			);
			path = Flashlight;
			sourceTree = "<group>";
		};
		A1000012 /* Products */ = {
			isa = PBXGroup;
			children = (
				A1000003,
			);
			name = Products;
			sourceTree = "<group>";
		};
/* End PBXGroup section */

/* Begin PBXNativeTarget section */
		A1000020 /* Flashlight */ = {
			isa = PBXNativeTarget;
			buildConfigurationList = A1000030;
			buildPhases = (
				A1000021,
			);
			buildRules = (
			);
			dependencies = (
			);
			name = Flashlight;
			productName = Flashlight;
			productReference = A1000003;
			productType = "com.apple.product-type.application";
		};
/* End PBXNativeTarget section */

/* Begin PBXProject section */
		A1000040 /* Project object */ = {
			isa = PBXProject;
			attributes = {
				BuildIndependentTargetsInParallel = 1;
				LastSwiftUpdateCheck = 1500;
				LastUpgradeCheck = 1500;
			};
			buildConfigurationList = A1000041;
			compatibilityVersion = "Xcode 14.0";
			developmentRegion = en;
			hasScannedForEncodings = 0;
			knownRegions = (
				en,
				Base,
			);
			mainGroup = A1000010;
			productRefGroup = A1000012;
			projectDirPath = "";
			projectRoot = "";
			targets = (
				A1000020,
			);
		};
/* End PBXProject section */

/* Begin PBXSourcesBuildPhase section */
		A1000021 /* Sources */ = {
			isa = PBXSourcesBuildPhase;
			buildActionMask = 2147483647;
			files = (
				A1000001,
			);
			runOnlyForDeploymentPostprocessing = 0;
		};
/* End PBXSourcesBuildPhase section */

/* Begin XCBuildConfiguration section */
		A1000050 /* Debug */ = {
			isa = XCBuildConfiguration;
			buildSettings = {
				ALWAYS_SEARCH_USER_PATHS = NO;
				CLANG_ENABLE_MODULES = YES;
				CLANG_ENABLE_OBJC_ARC = YES;
				CODE_SIGN_STYLE = Automatic;
				CURRENT_PROJECT_VERSION = 1;
				DEVELOPMENT_TEAM = "";
				GENERATE_INFOPLIST_FILE = YES;
				INFOPLIST_KEY_NSCameraUsageDescription = "Required to control the flashlight";
				INFOPLIST_KEY_UIApplicationSceneManifest_Generation = YES;
				INFOPLIST_KEY_UIApplicationSupportsIndirectInputEvents = YES;
				INFOPLIST_KEY_UILaunchScreen_Generation = YES;
				INFOPLIST_KEY_UISupportedInterfaceOrientations = UIInterfaceOrientationPortrait;
				IPHONEOS_DEPLOYMENT_TARGET = 16.0;
				LD_RUNPATH_SEARCH_PATHS = "@executable_path/Frameworks";
				MARKETING_VERSION = 1.0;
				PRODUCT_BUNDLE_IDENTIFIER = "com.marceausolutions.flashlight";
				PRODUCT_NAME = "$(TARGET_NAME)";
				SDKROOT = iphoneos;
				SWIFT_EMIT_LOC_STRINGS = YES;
				SWIFT_VERSION = 5.0;
				TARGETED_DEVICE_FAMILY = 1;
			};
			name = Debug;
		};
		A1000051 /* Release */ = {
			isa = XCBuildConfiguration;
			buildSettings = {
				ALWAYS_SEARCH_USER_PATHS = NO;
				CLANG_ENABLE_MODULES = YES;
				CLANG_ENABLE_OBJC_ARC = YES;
				CODE_SIGN_STYLE = Automatic;
				CURRENT_PROJECT_VERSION = 1;
				DEVELOPMENT_TEAM = "";
				GENERATE_INFOPLIST_FILE = YES;
				INFOPLIST_KEY_NSCameraUsageDescription = "Required to control the flashlight";
				INFOPLIST_KEY_UIApplicationSceneManifest_Generation = YES;
				INFOPLIST_KEY_UIApplicationSupportsIndirectInputEvents = YES;
				INFOPLIST_KEY_UILaunchScreen_Generation = YES;
				INFOPLIST_KEY_UISupportedInterfaceOrientations = UIInterfaceOrientationPortrait;
				IPHONEOS_DEPLOYMENT_TARGET = 16.0;
				LD_RUNPATH_SEARCH_PATHS = "@executable_path/Frameworks";
				MARKETING_VERSION = 1.0;
				PRODUCT_BUNDLE_IDENTIFIER = "com.marceausolutions.flashlight";
				PRODUCT_NAME = "$(TARGET_NAME)";
				SDKROOT = iphoneos;
				SWIFT_EMIT_LOC_STRINGS = YES;
				SWIFT_VERSION = 5.0;
				TARGETED_DEVICE_FAMILY = 1;
			};
			name = Release;
		};
		A1000052 /* Debug */ = {
			isa = XCBuildConfiguration;
			buildSettings = {
				ALWAYS_SEARCH_USER_PATHS = NO;
				CLANG_ENABLE_MODULES = YES;
				CLANG_ENABLE_OBJC_ARC = YES;
				COPY_PHASE_STRIP = NO;
				DEBUG_INFORMATION_FORMAT = dwarf;
				ENABLE_STRICT_OBJC_MSGSEND = YES;
				ENABLE_TESTABILITY = YES;
				GCC_DYNAMIC_NO_PIC = NO;
				GCC_OPTIMIZATION_LEVEL = 0;
				GCC_PREPROCESSOR_DEFINITIONS = (
					"DEBUG=1",
					"$(inherited)",
				);
				MTL_ENABLE_DEBUG_INFO = INCLUDE_SOURCE;
				ONLY_ACTIVE_ARCH = YES;
				SWIFT_ACTIVE_COMPILATION_CONDITIONS = DEBUG;
				SWIFT_OPTIMIZATION_LEVEL = "-Onone";
			};
			name = Debug;
		};
		A1000053 /* Release */ = {
			isa = XCBuildConfiguration;
			buildSettings = {
				ALWAYS_SEARCH_USER_PATHS = NO;
				CLANG_ENABLE_MODULES = YES;
				CLANG_ENABLE_OBJC_ARC = YES;
				COPY_PHASE_STRIP = NO;
				DEBUG_INFORMATION_FORMAT = "dwarf-with-dsym";
				ENABLE_NS_ASSERTIONS = NO;
				ENABLE_STRICT_OBJC_MSGSEND = YES;
				MTL_ENABLE_DEBUG_INFO = NO;
				SWIFT_COMPILATION_MODE = wholemodule;
				SWIFT_OPTIMIZATION_LEVEL = "-O";
				VALIDATE_PRODUCT = YES;
			};
			name = Release;
		};
/* End XCBuildConfiguration section */

/* Begin XCConfigurationList section */
		A1000030 /* Build configuration list for PBXNativeTarget "Flashlight" */ = {
			isa = XCConfigurationList;
			buildConfigurations = (
				A1000050,
				A1000051,
			);
			defaultConfigurationIsVisible = 0;
			defaultConfigurationName = Release;
		};
		A1000041 /* Build configuration list for PBXProject "Flashlight" */ = {
			isa = XCConfigurationList;
			buildConfigurations = (
				A1000052,
				A1000053,
			);
			defaultConfigurationIsVisible = 0;
			defaultConfigurationName = Release;
		};
/* End XCConfigurationList section */
	};
	rootObject = A1000040 /* Project object */;
}
PBXPROJ

echo "✅ Project created at ~/Desktop/$APP_NAME"
echo ""
echo "Next steps:"
echo "1. Open ~/Desktop/$APP_NAME/$APP_NAME.xcodeproj"
echo "2. Select your Team in Signing & Capabilities (your Apple ID)"
echo "3. Connect your iPhone and select it as the target"
echo "4. Press Cmd+R to build and run"
echo "5. On first run, go to Settings → General → VPN & Device Management → Trust the developer"
echo ""
echo "🎉 Done! The app will work for 7 days, then just rebuild."

open ~/Desktop/$APP_NAME/$APP_NAME.xcodeproj
