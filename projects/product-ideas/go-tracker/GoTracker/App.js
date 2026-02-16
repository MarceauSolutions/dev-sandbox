import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ScrollView,
  Platform,
} from 'react-native';
import * as Location from 'expo-location';
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import Svg, { Polyline, Circle, Polygon } from 'react-native-svg';

// Constants for performance tuning
const ELEVATION_SMOOTHING_THRESHOLD = 3; // meters - ignore elevation changes smaller than this
const MIN_DISTANCE_THRESHOLD = 0.001; // km - ~1 meter, ignore tiny movements (GPS noise)

export default function App() {
  const [tracking, setTracking] = useState(false);
  const [finished, setFinished] = useState(false);
  const [route, setRoute] = useState([]);
  const [stats, setStats] = useState({
    distance: 0,
    duration: 0,
    topSpeed: 0,
    avgSpeed: 0,
    pace: null,
    elevGain: 0,
    elevLoss: 0,
    minElev: null,
    maxElev: null,
  });
  const [displayTime, setDisplayTime] = useState(0);

  const locationSubscription = useRef(null);
  const startTimeRef = useRef(null);
  const timerRef = useRef(null);

  // Running totals for O(1) updates instead of O(n) recalculation
  const runningTotalsRef = useRef({
    distance: 0,
    elevGain: 0,
    elevLoss: 0,
    minElev: null,
    maxElev: null,
    speedSum: 0,
    speedCount: 0,
    maxSpeed: 0,
    lastSmoothedElev: null, // For elevation smoothing
  });

  const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371;
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLon = ((lon2 - lon1) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  };

  const formatPace = (decimalMinutes) => {
    if (!decimalMinutes || !isFinite(decimalMinutes) || decimalMinutes > 60)
      return '--:--';
    const mins = Math.floor(decimalMinutes);
    const secs = Math.round((decimalMinutes - mins) * 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatTime = (seconds) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0)
      return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const startTracking = async () => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission Denied', 'Location permission is required to track your ride.');
      return;
    }

    setTracking(true);
    setFinished(false);
    setRoute([]);
    setStats({
      distance: 0,
      duration: 0,
      topSpeed: 0,
      avgSpeed: 0,
      pace: null,
      elevGain: 0,
      elevLoss: 0,
      minElev: null,
      maxElev: null,
    });

    // Reset running totals for O(1) incremental updates
    runningTotalsRef.current = {
      distance: 0,
      elevGain: 0,
      elevLoss: 0,
      minElev: null,
      maxElev: null,
      speedSum: 0,
      speedCount: 0,
      maxSpeed: 0,
      lastSmoothedElev: null,
    };

    startTimeRef.current = Date.now();
    setDisplayTime(0);

    timerRef.current = setInterval(() => {
      setDisplayTime(Math.floor((Date.now() - startTimeRef.current) / 1000));
    }, 1000);

    locationSubscription.current = await Location.watchPositionAsync(
      {
        accuracy: Location.Accuracy.BestForNavigation,
        timeInterval: 1000,
        distanceInterval: 1,
      },
      (location) => {
        const newPoint = {
          lat: location.coords.latitude,
          lng: location.coords.longitude,
          elevation: location.coords.altitude,
          speed: location.coords.speed || 0,
          timestamp: Date.now(),
        };

        setRoute((prev) => {
          const totals = runningTotalsRef.current;

          // O(1) incremental distance calculation - only compute for new point
          if (prev.length > 0) {
            const lastPoint = prev[prev.length - 1];
            const segmentDist = calculateDistance(
              lastPoint.lat,
              lastPoint.lng,
              newPoint.lat,
              newPoint.lng
            );

            // Filter out GPS noise (tiny movements)
            if (segmentDist >= MIN_DISTANCE_THRESHOLD) {
              totals.distance += segmentDist;
            }

            // Elevation tracking with smoothing to reduce GPS noise
            if (newPoint.elevation != null && lastPoint.elevation != null) {
              // Use smoothed elevation to reduce noise
              if (totals.lastSmoothedElev === null) {
                totals.lastSmoothedElev = lastPoint.elevation;
              }

              const elevDiff = newPoint.elevation - totals.lastSmoothedElev;

              // Only count significant elevation changes (reduces GPS noise)
              if (Math.abs(elevDiff) >= ELEVATION_SMOOTHING_THRESHOLD) {
                if (elevDiff > 0) {
                  totals.elevGain += elevDiff;
                } else {
                  totals.elevLoss += Math.abs(elevDiff);
                }
                totals.lastSmoothedElev = newPoint.elevation;
              }
            }
          }

          // Update min/max elevation
          if (newPoint.elevation != null) {
            if (totals.minElev === null || newPoint.elevation < totals.minElev) {
              totals.minElev = newPoint.elevation;
            }
            if (totals.maxElev === null || newPoint.elevation > totals.maxElev) {
              totals.maxElev = newPoint.elevation;
            }
          }

          // Update speed stats
          if (newPoint.speed > 0) {
            const speedMph = newPoint.speed * 2.237;
            totals.maxSpeed = Math.max(totals.maxSpeed, speedMph);
            totals.speedSum += speedMph;
            totals.speedCount++;
          }

          // Calculate derived stats
          const durationHours = (Date.now() - startTimeRef.current) / 1000 / 3600;
          const distMiles = totals.distance * 0.621371;
          const calculatedAvg = durationHours > 0 ? distMiles / durationHours : 0;
          const avgSpeed = totals.speedCount > 0 ? totals.speedSum / totals.speedCount : calculatedAvg;
          const pace = avgSpeed > 0 ? 60 / avgSpeed : null;

          setStats({
            distance: distMiles,
            duration: (Date.now() - startTimeRef.current) / 1000,
            topSpeed: totals.maxSpeed,
            avgSpeed,
            pace,
            elevGain: totals.elevGain * 3.28084,
            elevLoss: totals.elevLoss * 3.28084,
            minElev: totals.minElev != null ? totals.minElev * 3.28084 : null,
            maxElev: totals.maxElev != null ? totals.maxElev * 3.28084 : null,
          });

          return [...prev, newPoint];
        });
      }
    );
  };

  const stopTracking = useCallback(() => {
    // Confirm before stopping to prevent accidental data loss
    Alert.alert(
      'Stop Tracking?',
      'Are you sure you want to stop? Your ride stats will be saved.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Stop',
          style: 'destructive',
          onPress: () => {
            if (locationSubscription.current) {
              locationSubscription.current.remove();
              locationSubscription.current = null;
            }
            if (timerRef.current) {
              clearInterval(timerRef.current);
            }
            setTracking(false);
            setFinished(true);
          },
        },
      ]
    );
  }, []);

  const reset = () => {
    setFinished(false);
    setRoute([]);
    setStats({
      distance: 0,
      duration: 0,
      topSpeed: 0,
      avgSpeed: 0,
      pace: null,
      elevGain: 0,
      elevLoss: 0,
      minElev: null,
      maxElev: null,
    });
    setDisplayTime(0);
  };

  const exportGPX = useCallback(async () => {
    try {
      const startDate = new Date(startTimeRef.current || Date.now());
      const gpxContent = `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="EUC Ride Tracker"
  xmlns="http://www.topografix.com/GPX/1/1">
  <metadata>
    <name>EUC Ride ${startDate.toLocaleDateString()}</name>
    <time>${startDate.toISOString()}</time>
  </metadata>
  <trk>
    <name>EUC Ride</name>
    <trkseg>
${route
  .map(
    (p) => `      <trkpt lat="${p.lat}" lon="${p.lng}">
${p.elevation != null ? `        <ele>${p.elevation.toFixed(1)}</ele>\n` : ''}        <time>${new Date(p.timestamp).toISOString()}</time>
      </trkpt>`
  )
  .join('\n')}
    </trkseg>
  </trk>
</gpx>`;

      const filename = `euc-ride-${startDate.toISOString().slice(0, 10)}.gpx`;
      const filepath = FileSystem.documentDirectory + filename;

      await FileSystem.writeAsStringAsync(filepath, gpxContent);

      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(filepath);
      } else {
        Alert.alert('Saved', `File saved to ${filepath}`);
      }
    } catch (error) {
      Alert.alert('Export Failed', 'Unable to export GPX file. Please try again.');
    }
  }, [route]);

  const exportJSON = useCallback(async () => {
    try {
      const startDate = new Date(startTimeRef.current || Date.now());
      const data = {
        date: startDate.toISOString(),
        app: 'EUC Ride Tracker',
        stats: {
          duration_seconds: stats.duration,
          distance_miles: stats.distance,
          avg_speed_mph: stats.avgSpeed,
          top_speed_mph: stats.topSpeed,
          pace_min_per_mile: stats.pace,
          elevation_gain_ft: stats.elevGain,
          elevation_loss_ft: stats.elevLoss,
          min_elevation_ft: stats.minElev,
          max_elevation_ft: stats.maxElev,
        },
        route: route.map((p) => ({
          lat: p.lat,
          lng: p.lng,
          elevation_m: p.elevation,
          speed_mps: p.speed,
          timestamp: new Date(p.timestamp).toISOString(),
        })),
      };

      const filename = `euc-ride-${startDate.toISOString().slice(0, 10)}.json`;
      const filepath = FileSystem.documentDirectory + filename;

      await FileSystem.writeAsStringAsync(filepath, JSON.stringify(data, null, 2));

      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(filepath);
      } else {
        Alert.alert('Saved', `File saved to ${filepath}`);
      }
    } catch (error) {
      Alert.alert('Export Failed', 'Unable to export JSON file. Please try again.');
    }
  }, [route, stats]);

  useEffect(() => {
    return () => {
      if (locationSubscription.current) {
        locationSubscription.current.remove();
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  // Memoized map view calculation - only recalculates when route changes
  const mapView = useMemo(() => {
    if (route.length === 0) return null;

    const lats = route.map((p) => p.lat);
    const lngs = route.map((p) => p.lng);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);

    const padding = 0.001;
    const width = 300;
    const height = 200;

    const latRange = Math.max(maxLat - minLat, 0.001) + padding * 2;
    const lngRange = Math.max(maxLng - minLng, 0.001) + padding * 2;

    const scale = Math.min(width / lngRange, height / latRange) * 0.8;
    const centerLat = (minLat + maxLat) / 2;
    const centerLng = (minLng + maxLng) / 2;

    const points = route
      .map((p) => {
        const x = (p.lng - centerLng) * scale + width / 2;
        const y = (centerLat - p.lat) * scale + height / 2;
        return `${x},${y}`;
      })
      .join(' ');

    const startX = (route[0].lng - centerLng) * scale + width / 2;
    const startY = (centerLat - route[0].lat) * scale + height / 2;
    const endX = (route[route.length - 1].lng - centerLng) * scale + width / 2;
    const endY = (centerLat - route[route.length - 1].lat) * scale + height / 2;

    return { points, startX, startY, endX, endY, width, height };
  }, [route]);

  // Memoized elevation profile - only recalculates when route changes
  const elevProfile = useMemo(() => {
    const elevPoints = route.filter((p) => p.elevation != null);
    if (elevPoints.length < 2) return null;

    const width = 300;
    const height = 80;
    const padding = 10;

    const elevs = elevPoints.map((p) => p.elevation * 3.28084);
    const minE = Math.min(...elevs);
    const maxE = Math.max(...elevs);
    const range = Math.max(maxE - minE, 10);

    const points = elevPoints
      .map((p, i) => {
        const x = padding + (i / (elevPoints.length - 1)) * (width - padding * 2);
        const y =
          height -
          padding -
          ((p.elevation * 3.28084 - minE) / range) * (height - padding * 2);
        return `${x},${y}`;
      })
      .join(' ');

    const areaPoints = `${padding},${height - padding} ${points} ${width - padding},${height - padding}`;

    return { points, areaPoints, width, height, minE, maxE };
  }, [route]);

  // Main GO button screen
  if (!tracking && !finished) {
    return (
      <View style={styles.container}>
        <TouchableOpacity style={styles.goButton} onPress={startTracking}>
          <Text style={styles.goButtonText}>GO</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Active tracking screen
  if (tracking) {
    const hasElevation = route.some((p) => p.elevation != null);

    return (
      <View style={styles.container}>
        <View style={styles.timerContainer}>
          <Text style={styles.timerText}>{formatTime(displayTime)}</Text>
          <Text style={styles.trackingLabel}>riding...</Text>
        </View>

        <View style={styles.statsRow}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{stats.distance.toFixed(2)}</Text>
            <Text style={styles.statLabel}>miles</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{stats.avgSpeed.toFixed(1)}</Text>
            <Text style={styles.statLabel}>avg mph</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{formatPace(stats.pace)}</Text>
            <Text style={styles.statLabel}>pace /mi</Text>
          </View>
        </View>

        {hasElevation && (
          <View style={styles.elevRow}>
            <View style={styles.statItem}>
              <Text style={styles.elevGain}>↑{Math.round(stats.elevGain)}</Text>
              <Text style={styles.statLabel}>ft gain</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.elevLoss}>↓{Math.round(stats.elevLoss)}</Text>
              <Text style={styles.statLabel}>ft loss</Text>
            </View>
          </View>
        )}

        <Text style={styles.pointsText}>{route.length} points recorded</Text>

        <TouchableOpacity style={styles.stopButton} onPress={stopTracking}>
          <Text style={styles.stopButtonText}>STOP</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Results screen
  const hasElevation = stats.minElev != null;

  return (
    <ScrollView style={styles.scrollContainer} contentContainerStyle={styles.resultsContainer}>
      <Text style={styles.completeText}>Ride Complete</Text>

      {/* Main Stats */}
      <View style={styles.card}>
        <View style={styles.statsGrid}>
          <View style={styles.statItem}>
            <Text style={styles.resultValue}>{formatTime(stats.duration)}</Text>
            <Text style={styles.statLabel}>total time</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.resultValue}>{stats.distance.toFixed(2)}</Text>
            <Text style={styles.statLabel}>miles</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.resultValue}>{stats.topSpeed.toFixed(1)}</Text>
            <Text style={styles.statLabel}>top mph</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.resultValue}>{stats.avgSpeed.toFixed(1)}</Text>
            <Text style={styles.statLabel}>avg mph</Text>
          </View>
        </View>

        <View style={styles.paceContainer}>
          <Text style={styles.resultValue}>{formatPace(stats.pace)}</Text>
          <Text style={styles.statLabel}>pace per mile</Text>
        </View>
      </View>

      {/* Elevation Stats */}
      {hasElevation && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Elevation</Text>
          <View style={styles.statsGrid}>
            <View style={styles.statItem}>
              <Text style={styles.elevGain}>↑{Math.round(stats.elevGain)}</Text>
              <Text style={styles.statLabel}>ft gained</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.elevLoss}>↓{Math.round(stats.elevLoss)}</Text>
              <Text style={styles.statLabel}>ft lost</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statValueSmall}>{Math.round(stats.minElev)}</Text>
              <Text style={styles.statLabel}>min ft</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statValueSmall}>{Math.round(stats.maxElev)}</Text>
              <Text style={styles.statLabel}>max ft</Text>
            </View>
          </View>

          {elevProfile && (
            <View style={styles.chartContainer}>
              <Svg width={elevProfile.width} height={elevProfile.height}>
                <Polygon
                  points={elevProfile.areaPoints}
                  fill="rgba(0, 212, 255, 0.2)"
                />
                <Polyline
                  points={elevProfile.points}
                  fill="none"
                  stroke="#00d4ff"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </Svg>
              <View style={styles.chartLabels}>
                <Text style={styles.chartLabel}>{Math.round(elevProfile.minE)} ft</Text>
                <Text style={styles.chartLabel}>{Math.round(elevProfile.maxE)} ft</Text>
              </View>
            </View>
          )}
        </View>
      )}

      {/* Route Map */}
      {mapView && route.length > 1 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Your Route</Text>
          <Svg width={mapView.width} height={mapView.height} style={styles.mapSvg}>
            <Polyline
              points={mapView.points}
              fill="none"
              stroke="#00d4ff"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <Circle cx={mapView.startX} cy={mapView.startY} r="6" fill="#00d4ff" />
            <Circle cx={mapView.endX} cy={mapView.endY} r="6" fill="#ef4444" />
          </Svg>
          <View style={styles.mapLegend}>
            <View style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: '#00d4ff' }]} />
              <Text style={styles.legendText}>start</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: '#ef4444' }]} />
              <Text style={styles.legendText}>end</Text>
            </View>
          </View>
        </View>
      )}

      {/* Export Buttons */}
      <View style={styles.exportRow}>
        <TouchableOpacity style={styles.exportButton} onPress={exportGPX}>
          <Text style={styles.exportButtonText}>Export GPX</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.exportButton} onPress={exportJSON}>
          <Text style={styles.exportButtonText}>Export JSON</Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity style={styles.goAgainButton} onPress={reset}>
        <Text style={styles.goAgainButtonText}>RIDE AGAIN</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#18181b',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
  },
  scrollContainer: {
    flex: 1,
    backgroundColor: '#18181b',
  },
  resultsContainer: {
    alignItems: 'center',
    padding: 24,
    paddingBottom: 48,
  },
  goButton: {
    width: 256,
    height: 256,
    borderRadius: 128,
    backgroundColor: '#00d4ff',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#00d4ff',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  goButtonText: {
    fontSize: 56,
    fontWeight: 'bold',
    color: 'white',
    letterSpacing: 4,
  },
  stopButton: {
    width: 160,
    height: 160,
    borderRadius: 80,
    backgroundColor: '#ef4444',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#ef4444',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  stopButtonText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: 'white',
  },
  timerContainer: {
    alignItems: 'center',
    marginBottom: 24,
  },
  timerText: {
    fontSize: 56,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: 'white',
    marginBottom: 8,
  },
  trackingLabel: {
    color: '#71717a',
    fontSize: 16,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 24,
    marginBottom: 16,
  },
  elevRow: {
    flexDirection: 'row',
    gap: 32,
    marginBottom: 16,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: 'white',
  },
  statValueSmall: {
    fontSize: 20,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: 'white',
  },
  statLabel: {
    color: '#71717a',
    fontSize: 12,
    marginTop: 4,
  },
  elevGain: {
    fontSize: 20,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: '#38bdf8',
  },
  elevLoss: {
    fontSize: 20,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: '#f87171',
  },
  pointsText: {
    color: '#52525b',
    fontSize: 14,
    marginBottom: 24,
  },
  completeText: {
    color: '#38bdf8',
    fontSize: 18,
    fontWeight: '500',
    marginBottom: 20,
  },
  card: {
    width: '100%',
    maxWidth: 350,
    backgroundColor: '#27272a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  cardTitle: {
    color: '#71717a',
    fontSize: 14,
    marginBottom: 12,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-around',
    gap: 16,
  },
  resultValue: {
    fontSize: 28,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: 'white',
  },
  paceContainer: {
    alignItems: 'center',
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#3f3f46',
  },
  chartContainer: {
    marginTop: 16,
  },
  chartLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  chartLabel: {
    color: '#52525b',
    fontSize: 12,
  },
  mapSvg: {
    alignSelf: 'center',
  },
  mapLegend: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  legendText: {
    color: '#52525b',
    fontSize: 12,
  },
  exportRow: {
    flexDirection: 'row',
    gap: 12,
    width: '100%',
    maxWidth: 350,
    marginBottom: 16,
  },
  exportButton: {
    flex: 1,
    backgroundColor: '#27272a',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  exportButtonText: {
    color: '#d4d4d8',
    fontSize: 14,
    fontWeight: '500',
  },
  goAgainButton: {
    backgroundColor: '#00d4ff',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 30,
    marginTop: 8,
  },
  goAgainButtonText: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold',
  },
});
