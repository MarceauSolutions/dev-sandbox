# Mobile App Implementation Example

This example shows how a React Native app would implement Uber/Lyft price comparison using mobile SDKs. **Note how it still requires REST API calls** - the SDKs only help with deep linking.

---

## React Native Implementation

### Installation

```bash
# Install dependencies
npm install react-native-uber-rides axios
npm install @react-native-community/geolocation

# iOS
cd ios && pod install && cd ..

# Note: No maintained React Native wrapper for Lyft SDK
# Would need to build custom native module or use deep links manually
```

---

## Full App Example

```javascript
// App.js - React Native Uber/Lyft Price Comparison
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Linking,
  Platform,
  Alert
} from 'react-native';
import axios from 'axios';

const UBER_SERVER_TOKEN = 'YOUR_UBER_SERVER_TOKEN';
const LYFT_CLIENT_ID = 'YOUR_LYFT_CLIENT_ID';
const LYFT_CLIENT_SECRET = 'YOUR_LYFT_CLIENT_SECRET';

// Example locations (San Francisco to San Jose)
const PICKUP = {
  latitude: 37.7749,
  longitude: -122.4194,
  address: 'San Francisco, CA'
};

const DROPOFF = {
  latitude: 37.3382,
  longitude: -121.8863,
  address: 'San Jose, CA'
};

const App = () => {
  const [uberPrices, setUberPrices] = useState([]);
  const [lyftPrices, setLyftPrices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPrices();
  }, []);

  // ============================================================
  // CRITICAL: STILL NEED REST APIs - SDKs DON'T PROVIDE PRICES!
  // ============================================================

  const fetchPrices = async () => {
    setLoading(true);
    await Promise.all([
      fetchUberPrices(),
      fetchLyftPrices()
    ]);
    setLoading(false);
  };

  // Fetch Uber prices via REST API (NOT SDK!)
  const fetchUberPrices = async () => {
    try {
      const response = await axios.get(
        'https://api.uber.com/v1.2/estimates/price',
        {
          params: {
            start_latitude: PICKUP.latitude,
            start_longitude: PICKUP.longitude,
            end_latitude: DROPOFF.latitude,
            end_longitude: DROPOFF.longitude
          },
          headers: {
            'Authorization': `Token ${UBER_SERVER_TOKEN}`,
            'Accept-Language': 'en_US',
            'Content-Type': 'application/json'
          }
        }
      );

      setUberPrices(response.data.prices);
    } catch (error) {
      console.error('Uber API Error:', error.response?.data || error.message);
      Alert.alert('Error', 'Failed to fetch Uber prices');
    }
  };

  // Fetch Lyft prices via REST API (NOT SDK!)
  const fetchLyftPrices = async () => {
    try {
      // First, get Lyft OAuth token using Client Credentials
      const tokenResponse = await axios.post(
        'https://api.lyft.com/oauth/token',
        'grant_type=client_credentials',
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          },
          auth: {
            username: LYFT_CLIENT_ID,
            password: LYFT_CLIENT_SECRET
          }
        }
      );

      const accessToken = tokenResponse.data.access_token;

      // Now fetch cost estimates
      const costResponse = await axios.get(
        'https://api.lyft.com/v1/cost',
        {
          params: {
            start_lat: PICKUP.latitude,
            start_lng: PICKUP.longitude,
            end_lat: DROPOFF.latitude,
            end_lng: DROPOFF.longitude
          },
          headers: {
            'Authorization': `Bearer ${accessToken}`
          }
        }
      );

      setLyftPrices(costResponse.data.cost_estimates);
    } catch (error) {
      console.error('Lyft API Error:', error.response?.data || error.message);
      Alert.alert('Error', 'Failed to fetch Lyft prices');
    }
  };

  // ============================================================
  // THIS IS WHERE SDKs ADD VALUE - Deep Linking to Native Apps
  // ============================================================

  const bookUberRide = async (productId) => {
    const uberAppURL = `uber://?client_id=${UBER_SERVER_TOKEN}&` +
      `action=setPickup&` +
      `pickup[latitude]=${PICKUP.latitude}&` +
      `pickup[longitude]=${PICKUP.longitude}&` +
      `dropoff[latitude]=${DROPOFF.latitude}&` +
      `dropoff[longitude]=${DROPOFF.longitude}&` +
      `product_id=${productId}`;

    const uberWebURL = `https://m.uber.com/ul/?` +
      `client_id=${UBER_SERVER_TOKEN}&` +
      `action=setPickup&` +
      `pickup[latitude]=${PICKUP.latitude}&` +
      `pickup[longitude]=${PICKUP.longitude}&` +
      `dropoff[latitude]=${DROPOFF.latitude}&` +
      `dropoff[longitude]=${DROPOFF.longitude}&` +
      `product_id=${productId}`;

    // Try to open Uber app, fallback to mobile web
    const canOpenApp = await Linking.canOpenURL(uberAppURL);
    if (canOpenApp) {
      await Linking.openURL(uberAppURL);
    } else {
      await Linking.openURL(uberWebURL);
    }
  };

  const bookLyftRide = async (rideType) => {
    const lyftAppURL = `lyft://ridetype?` +
      `id=${rideType}&` +
      `partner=${LYFT_CLIENT_ID}&` +
      `pickup[latitude]=${PICKUP.latitude}&` +
      `pickup[longitude]=${PICKUP.longitude}&` +
      `destination[latitude]=${DROPOFF.latitude}&` +
      `destination[longitude]=${DROPOFF.longitude}`;

    const lyftWebURL = `https://lyft.com/ride?` +
      `id=${rideType}&` +
      `partner=${LYFT_CLIENT_ID}&` +
      `pickup[latitude]=${PICKUP.latitude}&` +
      `pickup[longitude]=${PICKUP.longitude}&` +
      `destination[latitude]=${DROPOFF.latitude}&` +
      `destination[longitude]=${DROPOFF.longitude}`;

    // Try to open Lyft app, fallback to mobile web
    const canOpenApp = await Linking.canOpenURL(lyftAppURL);
    if (canOpenApp) {
      await Linking.openURL(lyftAppURL);
    } else {
      await Linking.openURL(lyftWebURL);
    }
  };

  // ============================================================
  // UI Rendering
  // ============================================================

  if (loading) {
    return (
      <View style={styles.container}>
        <Text style={styles.loadingText}>Loading prices...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Ride Price Comparison</Text>

      <View style={styles.locationContainer}>
        <Text style={styles.locationLabel}>From:</Text>
        <Text style={styles.locationText}>{PICKUP.address}</Text>
        <Text style={styles.locationLabel}>To:</Text>
        <Text style={styles.locationText}>{DROPOFF.address}</Text>
      </View>

      {/* Uber Prices */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Uber Options</Text>
        {uberPrices.map((price, index) => (
          <View key={index} style={styles.priceCard}>
            <View style={styles.priceInfo}>
              <Text style={styles.productName}>{price.display_name}</Text>
              <Text style={styles.priceText}>{price.estimate}</Text>
              <Text style={styles.durationText}>
                {price.duration / 60} min • {(price.distance * 0.000621371).toFixed(1)} miles
              </Text>
            </View>
            <TouchableOpacity
              style={styles.bookButton}
              onPress={() => bookUberRide(price.product_id)}
            >
              <Text style={styles.bookButtonText}>Book Uber</Text>
            </TouchableOpacity>
          </View>
        ))}
      </View>

      {/* Lyft Prices */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Lyft Options</Text>
        {lyftPrices.map((price, index) => (
          <View key={index} style={styles.priceCard}>
            <View style={styles.priceInfo}>
              <Text style={styles.productName}>{price.display_name}</Text>
              <Text style={styles.priceText}>
                ${(price.estimated_cost_cents_min / 100).toFixed(2)} -
                ${(price.estimated_cost_cents_max / 100).toFixed(2)}
              </Text>
              <Text style={styles.durationText}>
                {Math.round(price.estimated_duration_seconds / 60)} min
              </Text>
            </View>
            <TouchableOpacity
              style={[styles.bookButton, styles.lyftButton]}
              onPress={() => bookLyftRide(price.ride_type)}
            >
              <Text style={styles.bookButtonText}>Book Lyft</Text>
            </TouchableOpacity>
          </View>
        ))}
      </View>

      <TouchableOpacity style={styles.refreshButton} onPress={fetchPrices}>
        <Text style={styles.refreshButtonText}>Refresh Prices</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 20,
    paddingTop: Platform.OS === 'ios' ? 60 : 40
  },
  loadingText: {
    fontSize: 18,
    textAlign: 'center',
    marginTop: 100
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center'
  },
  locationContainer: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20
  },
  locationLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 5
  },
  locationText: {
    fontSize: 16,
    marginBottom: 5
  },
  section: {
    marginBottom: 20
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 10
  },
  priceCard: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  priceInfo: {
    flex: 1
  },
  productName: {
    fontSize: 16,
    fontWeight: 'bold'
  },
  priceText: {
    fontSize: 18,
    color: '#2ecc71',
    marginTop: 5
  },
  durationText: {
    fontSize: 12,
    color: '#666',
    marginTop: 5
  },
  bookButton: {
    backgroundColor: '#000',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 5
  },
  lyftButton: {
    backgroundColor: '#FF00BF'
  },
  bookButtonText: {
    color: 'white',
    fontWeight: 'bold'
  },
  refreshButton: {
    backgroundColor: '#3498db',
    padding: 15,
    borderRadius: 10,
    marginTop: 20
  },
  refreshButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'center'
  }
});

export default App;
```

---

## iOS Configuration

### Info.plist (Required for Deep Linking)

```xml
<!-- Add to ios/YourApp/Info.plist -->
<key>LSApplicationQueriesSchemes</key>
<array>
    <string>uber</string>
    <string>lyft</string>
</array>

<!-- Allow HTTP requests to APIs -->
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <true/>
</dict>

<!-- Location permissions (if you want to auto-detect pickup) -->
<key>NSLocationWhenInUseUsageDescription</key>
<string>We need your location to find rides near you</string>
```

---

## Android Configuration

### AndroidManifest.xml

```xml
<!-- Add to android/app/src/main/AndroidManifest.xml -->
<manifest>
    <application>
        <!-- Intent filters for deep linking -->
        <activity>
            <intent-filter>
                <action android:name="android.intent.action.VIEW" />
                <category android:name="android.intent.category.DEFAULT" />
                <category android:name="android.intent.category.BROWSABLE" />
                <data android:scheme="uber" />
                <data android:scheme="lyft" />
            </intent-filter>
        </activity>
    </application>

    <!-- Location permissions (if you want to auto-detect pickup) -->
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
</manifest>
```

---

## Key Observations

### What This Code Demonstrates

1. **REST APIs still required** (lines 52-126)
   - `fetchUberPrices()` calls Uber REST API directly
   - `fetchLyftPrices()` calls Lyft REST API directly
   - **Mobile SDKs don't provide this functionality**

2. **Deep linking is simple** (lines 132-176)
   - Just URL schemes: `uber://` and `lyft://`
   - Fallback to mobile web if app not installed
   - **This is the ONLY value SDKs add** - and you can do it manually!

3. **No SDK dependencies needed**
   - React Native built-in `Linking` API handles deep links
   - `axios` for API calls (same as web)
   - **You could build this exact app without any Uber/Lyft SDKs**

### The SDKs Don't Actually Help

```javascript
// With Uber SDK (theoretical):
import { UberButton } from 'react-native-uber-rides';
<UberButton onPress={bookUber} /> // Just a fancy deep link button

// Without SDK (what we did above):
import { Linking } from 'react-native';
Linking.openURL('uber://...') // Same result, zero dependencies
```

**Conclusion:** The mobile SDK approach is **functionally identical** to web approach for price comparison, but with 10x the complexity.

---

## Alternative: Mobile-Responsive Web App

Instead of building a native mobile app, you could build a responsive web app:

```javascript
// Same API calls, but in a React web app
const fetchPrices = async () => {
  // Identical REST API calls as mobile
  const uber = await fetch('https://api.uber.com/v1.2/estimates/price...');
  const lyft = await fetch('https://api.lyft.com/v1/cost...');
  // Display results
};

// Deep linking still works from web
const bookUber = () => {
  // Try Uber app first
  window.location.href = 'uber://...';
  // Fallback to mobile web after 500ms
  setTimeout(() => {
    window.location.href = 'https://m.uber.com/ul/...';
  }, 500);
};
```

**Advantages:**
- ✅ No app store approval
- ✅ Instant access (no download)
- ✅ Works on desktop too
- ✅ Much easier to maintain
- ✅ Same functionality as mobile app
- ✅ "Add to Home Screen" for app-like experience

**Result:** 80% of the mobile UX, 20% of the development effort.

---

## Build & Run

```bash
# Install dependencies
npm install

# iOS
npx react-native run-ios

# Android
npx react-native run-android

# Note: Replace YOUR_UBER_SERVER_TOKEN, LYFT_CLIENT_ID, LYFT_CLIENT_SECRET
# with real credentials from developer portals
```

---

## Performance Comparison

| Metric | Native App | Mobile Web |
|--------|-----------|------------|
| **Development time** | 4-8 weeks | 1-2 weeks |
| **Code complexity** | ~5000 lines | ~1000 lines |
| **Bundle size** | 50-100 MB | <1 MB |
| **Load time** | 2-5 sec | <1 sec |
| **Distribution** | App store | URL |
| **Updates** | App store review | Instant |
| **Maintenance** | High | Low |

**Verdict:** Mobile web wins for this use case.
