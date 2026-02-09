#!/usr/bin/env python3
"""
Aggregate Multiple Test Sessions

Combines data from multiple quote collection sessions to calculate
aggregate accuracy metrics with statistical confidence.

Usage:
    python3 aggregate_sessions.py

Expects session files in output/sessions/ directory:
    output/sessions/session-1/actual-quotes-session-1.csv
    output/sessions/session-2/actual-quotes-session-2.csv
    output/sessions/session-3/actual-quotes-session-3.csv
"""

import csv
import os
import sys
import statistics
from datetime import datetime
from typing import Dict, List
from collections import defaultdict


def find_session_files(base_dir: str) -> List[str]:
    """Find all session CSV files"""
    sessions_dir = os.path.join(base_dir, 'output', 'sessions')
    session_files = []

    if not os.path.exists(sessions_dir):
        return session_files

    for session_folder in sorted(os.listdir(sessions_dir)):
        folder_path = os.path.join(sessions_dir, session_folder)
        if os.path.isdir(folder_path):
            for filename in os.listdir(folder_path):
                if filename.startswith('actual-quotes') and filename.endswith('.csv'):
                    session_files.append(os.path.join(folder_path, filename))

    return session_files


def load_session(filepath: str) -> Dict:
    """Load a single session's data"""
    data = {}
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            route_id = row['route_id']
            if row.get('actual_uber') and row.get('actual_lyft'):
                try:
                    data[route_id] = {
                        'actual_uber': float(row['actual_uber']),
                        'actual_lyft': float(row['actual_lyft']),
                        'surge_active': row.get('surge_active', 'unknown'),
                        'timestamp': row.get('timestamp', ''),
                    }
                except ValueError:
                    continue
    return data


def load_estimates(workspace_dir: str) -> Dict:
    """Load algorithm estimates"""
    estimates_path = os.path.join(workspace_dir, 'estimated-quotes.csv')
    estimates = {}

    with open(estimates_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            route_id = row['route_id']
            estimates[route_id] = {
                'uber_estimate': float(row['uber_estimate']),
                'lyft_estimate': float(row['lyft_estimate']),
                'city': row['city'],
                'distance_category': row['distance_category'],
            }

    return estimates


def aggregate_sessions(session_files: List[str]) -> Dict:
    """Aggregate data from multiple sessions"""
    aggregated = defaultdict(lambda: {'uber': [], 'lyft': [], 'surge': []})

    for filepath in session_files:
        session_data = load_session(filepath)
        session_name = os.path.basename(os.path.dirname(filepath))

        for route_id, data in session_data.items():
            aggregated[route_id]['uber'].append(data['actual_uber'])
            aggregated[route_id]['lyft'].append(data['actual_lyft'])
            aggregated[route_id]['surge'].append(data['surge_active'])

    return dict(aggregated)


def calculate_aggregate_accuracy(estimates: Dict, aggregated: Dict) -> Dict:
    """Calculate accuracy metrics across all sessions"""
    results = {
        'routes': [],
        'uber_errors': [],
        'lyft_errors': [],
        'recommendation_correct': [],
    }

    for route_id, samples in aggregated.items():
        if route_id not in estimates:
            continue

        est = estimates[route_id]
        uber_actuals = samples['uber']
        lyft_actuals = samples['lyft']

        if not uber_actuals or not lyft_actuals:
            continue

        # Use median of samples for comparison
        median_uber = statistics.median(uber_actuals)
        median_lyft = statistics.median(lyft_actuals)

        # Calculate errors
        uber_error_pct = abs(est['uber_estimate'] - median_uber) / median_uber * 100
        lyft_error_pct = abs(est['lyft_estimate'] - median_lyft) / median_lyft * 100

        # Calculate variance
        uber_variance = max(uber_actuals) - min(uber_actuals) if len(uber_actuals) > 1 else 0
        lyft_variance = max(lyft_actuals) - min(lyft_actuals) if len(lyft_actuals) > 1 else 0

        # Check recommendation
        est_recommendation = 'lyft' if est['lyft_estimate'] < est['uber_estimate'] else 'uber'
        actual_best = 'lyft' if median_lyft < median_uber else 'uber'
        recommendation_correct = est_recommendation == actual_best

        results['routes'].append({
            'route_id': route_id,
            'city': est['city'],
            'distance_category': est['distance_category'],
            'samples': len(uber_actuals),
            'est_uber': est['uber_estimate'],
            'median_uber': round(median_uber, 2),
            'uber_error_pct': round(uber_error_pct, 1),
            'uber_variance': round(uber_variance, 2),
            'est_lyft': est['lyft_estimate'],
            'median_lyft': round(median_lyft, 2),
            'lyft_error_pct': round(lyft_error_pct, 1),
            'lyft_variance': round(lyft_variance, 2),
            'recommendation_correct': recommendation_correct,
        })

        results['uber_errors'].append(uber_error_pct)
        results['lyft_errors'].append(lyft_error_pct)
        results['recommendation_correct'].append(recommendation_correct)

    return results


def generate_aggregate_report(results: Dict, num_sessions: int, output_path: str):
    """Generate comprehensive aggregate report"""
    total_routes = len(results['routes'])

    uber_within_20 = sum(1 for e in results['uber_errors'] if e <= 20)
    lyft_within_20 = sum(1 for e in results['lyft_errors'] if e <= 20)
    correct_recs = sum(results['recommendation_correct'])

    uber_accuracy = round(100 * uber_within_20 / total_routes, 1) if total_routes else 0
    lyft_accuracy = round(100 * lyft_within_20 / total_routes, 1) if total_routes else 0
    overall_accuracy = round(100 * (uber_within_20 + lyft_within_20) / (2 * total_routes), 1) if total_routes else 0
    rec_accuracy = round(100 * correct_recs / total_routes, 1) if total_routes else 0

    report = f"""# Aggregate Accuracy Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Sessions Analyzed:** {num_sessions}
**Routes per Session:** {total_routes}
**Total Data Points:** {total_routes * num_sessions * 2} (routes × sessions × services)

---

## Executive Summary

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Uber within 20% | 85% | {uber_accuracy}% | {'PASS' if uber_accuracy >= 85 else 'FAIL'} |
| Lyft within 20% | 85% | {lyft_accuracy}% | {'PASS' if lyft_accuracy >= 85 else 'FAIL'} |
| Overall Accuracy | 85% | {overall_accuracy}% | {'PASS' if overall_accuracy >= 85 else 'FAIL'} |
| Recommendation Accuracy | 85% | {rec_accuracy}% | {'PASS' if rec_accuracy >= 85 else 'FAIL'} |

---

## Statistical Summary

### Uber Estimates
- Mean Error: {round(statistics.mean(results['uber_errors']), 1)}%
- Median Error: {round(statistics.median(results['uber_errors']), 1)}%
- Within 20%: {uber_within_20}/{total_routes} routes

### Lyft Estimates
- Mean Error: {round(statistics.mean(results['lyft_errors']), 1)}%
- Median Error: {round(statistics.median(results['lyft_errors']), 1)}%
- Within 20%: {lyft_within_20}/{total_routes} routes

---

## Variance Analysis

High variance indicates inconsistent pricing (likely surge-related).

| Variance Level | Uber Routes | Lyft Routes |
|----------------|-------------|-------------|
| Low (<$2) | {sum(1 for r in results['routes'] if r['uber_variance'] < 2)} | {sum(1 for r in results['routes'] if r['lyft_variance'] < 2)} |
| Medium ($2-5) | {sum(1 for r in results['routes'] if 2 <= r['uber_variance'] < 5)} | {sum(1 for r in results['routes'] if 2 <= r['lyft_variance'] < 5)} |
| High (>$5) | {sum(1 for r in results['routes'] if r['uber_variance'] >= 5)} | {sum(1 for r in results['routes'] if r['lyft_variance'] >= 5)} |

---

## Route-Level Results

| Route | City | Dist | Samples | Est Uber | Med Uber | Err% | Var | Est Lyft | Med Lyft | Err% | Var | Rec OK |
|-------|------|------|---------|----------|----------|------|-----|----------|----------|------|-----|--------|
"""

    for r in sorted(results['routes'], key=lambda x: int(x['route_id'])):
        rec_ok = 'YES' if r['recommendation_correct'] else 'NO'
        report += f"| {r['route_id']} | {r['city'][:8]} | {r['distance_category'][:3]} | {r['samples']} | ${r['est_uber']:.0f} | ${r['median_uber']:.0f} | {r['uber_error_pct']}% | ${r['uber_variance']:.0f} | ${r['est_lyft']:.0f} | ${r['median_lyft']:.0f} | {r['lyft_error_pct']}% | ${r['lyft_variance']:.0f} | {rec_ok} |\n"

    # Add by-city analysis
    by_city = defaultdict(lambda: {'uber_errors': [], 'lyft_errors': [], 'correct': 0, 'total': 0})
    for r in results['routes']:
        city = r['city']
        by_city[city]['uber_errors'].append(r['uber_error_pct'])
        by_city[city]['lyft_errors'].append(r['lyft_error_pct'])
        by_city[city]['correct'] += 1 if r['recommendation_correct'] else 0
        by_city[city]['total'] += 1

    report += """
---

## Analysis by City

| City | Uber Err | Lyft Err | Rec Acc | Routes |
|------|----------|----------|---------|--------|
"""

    for city in sorted(by_city.keys()):
        data = by_city[city]
        uber_mean = round(statistics.mean(data['uber_errors']), 1)
        lyft_mean = round(statistics.mean(data['lyft_errors']), 1)
        rec_acc = round(100 * data['correct'] / data['total'], 0)
        report += f"| {city} | {uber_mean}% | {lyft_mean}% | {rec_acc}% | {data['total']} |\n"

    report += """
---

## Confidence Assessment

Based on {num_sessions} sessions with {total_routes} routes each:

- **Sample Size:** {total_samples} total observations
- **Statistical Power:** {power}
- **Confidence Level:** 95%

### Interpretation

"""

    total_samples = total_routes * num_sessions * 2
    if total_samples >= 180:
        power = "Excellent (≥180 samples)"
        interpretation = "Results are statistically robust and can be used for production decisions."
    elif total_samples >= 90:
        power = "Good (90-179 samples)"
        interpretation = "Results are reliable but consider additional session for high-stakes decisions."
    else:
        power = "Moderate (<90 samples)"
        interpretation = "Consider collecting additional sessions before production launch."

    report = report.format(
        num_sessions=num_sessions,
        total_routes=total_routes,
        total_samples=total_samples,
        power=power
    )
    report += interpretation

    report += """

---

## Recommendations

"""

    if overall_accuracy >= 85 and rec_accuracy >= 85:
        report += "### READY FOR PRODUCTION\n\nAlgorithm meets all accuracy targets. Proceed with deployment.\n"
    elif overall_accuracy >= 75:
        report += "### NEEDS MINOR IMPROVEMENTS\n\nReview high-error cities and update rate cards before production.\n"
    else:
        report += "### NEEDS MAJOR IMPROVEMENTS\n\nSignificant recalibration required before production.\n"

    # Identify problem areas
    problem_cities = [city for city, data in by_city.items()
                      if statistics.mean(data['uber_errors']) > 25 or statistics.mean(data['lyft_errors']) > 25]

    if problem_cities:
        report += f"\n**Cities needing attention:** {', '.join(problem_cities)}\n"

    high_variance_routes = [r['route_id'] for r in results['routes']
                            if r['uber_variance'] >= 5 or r['lyft_variance'] >= 5]

    if high_variance_routes:
        report += f"\n**High-variance routes:** {', '.join(high_variance_routes)}\n"

    report += """
---

*Generated by aggregate_sessions.py*
"""

    with open(output_path, 'w') as f:
        f.write(report)

    print(f"Aggregate report generated: {output_path}")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)

    # Find session files
    session_files = find_session_files(base_dir)

    if not session_files:
        print("No session files found.")
        print("\nExpected location: output/sessions/session-X/actual-quotes-*.csv")
        print("\nTo set up sessions:")
        print("  1. mkdir -p output/sessions/session-1")
        print("  2. cp workspace/actual-quotes.csv output/sessions/session-1/actual-quotes-session-1.csv")
        print("  3. Repeat for additional sessions")
        sys.exit(1)

    print(f"Found {len(session_files)} session files:")
    for f in session_files:
        print(f"  - {f}")

    # Load estimates
    estimates = load_estimates(script_dir)
    print(f"\nLoaded {len(estimates)} route estimates")

    # Aggregate sessions
    aggregated = aggregate_sessions(session_files)
    print(f"Aggregated data for {len(aggregated)} routes")

    # Calculate accuracy
    results = calculate_aggregate_accuracy(estimates, aggregated)

    if not results['routes']:
        print("ERROR: No valid comparison data found.")
        sys.exit(1)

    # Generate report
    output_path = os.path.join(base_dir, 'output', 'AGGREGATE-ACCURACY-REPORT.md')
    generate_aggregate_report(results, len(session_files), output_path)

    # Print summary
    total = len(results['routes'])
    uber_ok = sum(1 for e in results['uber_errors'] if e <= 20)
    lyft_ok = sum(1 for e in results['lyft_errors'] if e <= 20)
    overall = round(100 * (uber_ok + lyft_ok) / (2 * total), 1)

    print("\n" + "=" * 50)
    print("AGGREGATE ACCURACY SUMMARY")
    print("=" * 50)
    print(f"Sessions analyzed: {len(session_files)}")
    print(f"Overall accuracy: {overall}% within 20%")
    print(f"Status: {'PASS' if overall >= 85 else 'NEEDS IMPROVEMENT'}")
    print(f"\nFull report: {output_path}")


if __name__ == "__main__":
    main()
