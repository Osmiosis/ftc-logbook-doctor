"""Intelligence engine for diagnosing robot issues"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import timedelta
from typing import Dict, List, Tuple, Optional


class DiagnosticResult:
    """Container for diagnostic findings"""
    def __init__(self):
        self.high_current_events: List[Dict] = []
        self.motor_timeout_events: List[Dict] = []
        self.battery_prediction: Optional[Dict] = None
        self.compute_stability: Optional[Dict] = None
        self.critical_issues: List[str] = []
        self.warnings: List[str] = []
        self.recommendations: List[str] = []
        self.health_score: int = 100


def diagnose_issues(df: pd.DataFrame) -> DiagnosticResult:
    """
    Intelligent correlation of log events to identify root causes
    
    Args:
        df: Parsed log data DataFrame
        
    Returns:
        DiagnosticResult with correlated findings and predictions
    """
    result = DiagnosticResult()
    
    if df.empty:
        return result
    
    result = _analyze_battery_correlation(df, result)
    result = _predict_battery_life(df, result)
    result = _analyze_performance_degradation(df, result)
    result = _calculate_compute_efficiency(df, result)
    result = _analyze_disconnect_patterns(df, result)
    result = _calculate_health_score(result)
    result = _generate_recommendations(result)
    
    return result


def _analyze_battery_correlation(df: pd.DataFrame, result: DiagnosticResult) -> DiagnosticResult:
    """Detect battery drops near motor timeouts"""
    # Get battery readings with voltage
    battery_df = df[df['battery_voltage'].notna()].copy()
    
    if len(battery_df) < 2:
        return result
    
    # Calculate voltage changes
    battery_df['voltage_drop'] = battery_df['battery_voltage'].diff().abs()
    battery_df['time_diff'] = battery_df['datetime'].diff().dt.total_seconds() * 1000  # milliseconds
    
    # Find significant voltage drops (>1V)
    significant_drops = battery_df[battery_df['voltage_drop'] > 1.0]
    
    # Look for motor timeouts or errors in the full log
    motor_issues = df[
        df['message'].str.contains('timeout|Motor|comm timeout|could not read', case=False, na=False)
    ]
    
    # Correlate: Find motor issues within 500ms of battery drops
    for _, drop_row in significant_drops.iterrows():
        drop_time = drop_row['datetime']
        time_window_start = drop_time - timedelta(milliseconds=500)
        time_window_end = drop_time + timedelta(milliseconds=500)
        
        # Find motor issues in this time window
        nearby_motor_issues = motor_issues[
            (motor_issues['datetime'] >= time_window_start) &
            (motor_issues['datetime'] <= time_window_end)
        ]
        
        if len(nearby_motor_issues) > 0:
            # HIGH CURRENT DRAW EVENT DETECTED!
            event = {
                'timestamp': drop_time,
                'voltage_drop': drop_row['voltage_drop'],
                'voltage_before': drop_row['battery_voltage'] + drop_row['voltage_drop'],
                'voltage_after': drop_row['battery_voltage'],
                'motor_issues': nearby_motor_issues['message'].tolist(),
                'severity': 'CRITICAL' if drop_row['voltage_drop'] > 1.5 else 'HIGH'
            }
            result.high_current_events.append(event)
            result.critical_issues.append(
                f"High current draw detected at {drop_time.strftime('%H:%M:%S')}: "
                f"{drop_row['voltage_drop']:.2f}V drop correlated with motor timeout"
            )
    
    # Analyze overall battery drain rate
    if len(battery_df) > 1:
        total_drop = battery_df['battery_voltage'].iloc[0] - battery_df['battery_voltage'].iloc[-1]
        time_span = (battery_df['datetime'].iloc[-1] - battery_df['datetime'].iloc[0]).total_seconds()
        
        if time_span > 0:
            drain_rate = (total_drop / time_span) * 60  # volts per minute
            
            if drain_rate > 0.5:  # More than 0.5V per minute
                result.warnings.append(
                    f"High battery drain rate: {drain_rate:.2f}V/min "
                    f"(expected: ~0.2-0.3V/min for normal operation)"
                )
    
    return result


def _predict_battery_life(df: pd.DataFrame, result: DiagnosticResult) -> DiagnosticResult:
    """Predict if battery will last full 2.5 min match"""
    battery_df = df[df['battery_voltage'].notna()].copy()
    
    if len(battery_df) < 3:
        return result
    
    # Prepare data for sklearn
    battery_df['seconds_elapsed'] = (
        battery_df['datetime'] - battery_df['datetime'].iloc[0]
    ).dt.total_seconds()
    
    X = battery_df['seconds_elapsed'].values.reshape(-1, 1)
    y = battery_df['battery_voltage'].values
    
    # Train linear regression model
    model = LinearRegression()
    model.fit(X, y)
    
    # Predict voltage at 2.5 minutes (150 seconds)
    match_duration = 150  # seconds
    predicted_voltage = model.predict([[match_duration]])[0]
    
    # Get current trajectory
    current_time = battery_df['seconds_elapsed'].iloc[-1]
    current_voltage = battery_df['battery_voltage'].iloc[-1]
    
    # Calculate R² score (how well the trend fits)
    r2_score = model.score(X, y)
    
    result.battery_prediction = {
        'predicted_voltage_at_150s': predicted_voltage,
        'current_voltage': current_voltage,
        'current_time': current_time,
        'drain_rate_per_second': abs(model.coef_[0]),
        'will_survive_match': predicted_voltage > 11.5,  # 11.5V is critical cutoff
        'confidence': r2_score,
        'model': model
    }
    
    # Generate insight
    if predicted_voltage < 11.5:
        result.critical_issues.append(
            f"CRITICAL: Battery predicted to reach {predicted_voltage:.2f}V at 2:30 mark "
            f"(below 11.5V cutoff). Robot may not complete match!"
        )
    elif predicted_voltage < 12.0:
        result.warnings.append(
            f"Battery will be low at match end: ~{predicted_voltage:.2f}V predicted at 2:30"
        )
    
    return result


def _analyze_performance_degradation(df: pd.DataFrame, result: DiagnosticResult) -> DiagnosticResult:
    """Detect increasing loop times over session"""
    loop_df = df[df['loop_time_ms'].notna()].copy()
    
    if len(loop_df) < 5:
        return result
    
    # Calculate moving average to smooth out noise
    loop_df['loop_time_ma'] = loop_df['loop_time_ms'].rolling(window=3, min_periods=1).mean()
    
    # Check if loop times are trending upward
    first_half = loop_df.iloc[:len(loop_df)//2]['loop_time_ma'].mean()
    second_half = loop_df.iloc[len(loop_df)//2:]['loop_time_ma'].mean()
    
    degradation = second_half - first_half
    
    if degradation > 10:  # More than 10ms increase
        result.warnings.append(
            f"Performance degradation detected: Loop times increased by {degradation:.1f}ms "
            f"over session (from {first_half:.1f}ms to {second_half:.1f}ms avg)"
        )
    
    # Check for spikes
    spikes = loop_df[loop_df['loop_time_ms'] > 100]
    if len(spikes) > 0:
        result.warnings.append(
            f"{len(spikes)} severe loop time spikes detected (>100ms). "
            f"Max: {loop_df['loop_time_ms'].max():.1f}ms"
        )
    
    return result


def _calculate_compute_efficiency(df: pd.DataFrame, result: DiagnosticResult) -> DiagnosticResult:
    """Analyze loop time stability and detect software bottlenecks"""
    loop_df = df[df['loop_time_ms'].notna()].copy()
    
    if len(loop_df) < 10:
        return result
    
    loop_times = loop_df['loop_time_ms'].values
    mean_loop = np.mean(loop_times)
    std_loop = np.std(loop_times)
    
    # Coefficient of Variation (CV)
    cv = std_loop / mean_loop if mean_loop > 0 else 0
    
    # Blocking spikes (>3 standard deviations)
    threshold = mean_loop + (3 * std_loop)
    blocking_spikes = loop_times[loop_times > threshold]
    spike_count = len(blocking_spikes)
    spike_percentage = (spike_count / len(loop_times)) * 100
    
    # Detect periodic latency
    periodic_latency = False
    if spike_count > 3:
        spike_indices = np.where(loop_times > threshold)[0]
        if len(spike_indices) > 1:
            intervals = np.diff(spike_indices)
            interval_cv = np.std(intervals) / np.mean(intervals) if np.mean(intervals) > 0 else float('inf')
            # If intervals have low variance, they're periodic
            if interval_cv < 0.3 and np.mean(intervals) > 5:
                periodic_latency = True
    
    # Compute efficiency score (0-100)
    score = 100
    
    # Deduct for high jitter
    if cv > 0.5:
        score -= 30
    elif cv > 0.3:
        score -= 20
    elif cv > 0.2:
        score -= 10
    
    # Deduct for frequent blocking spikes
    if spike_percentage > 10:
        score -= 25
    elif spike_percentage > 5:
        score -= 15
    elif spike_percentage > 2:
        score -= 5
    
    # Deduct for periodic latency
    if periodic_latency:
        score -= 15
    
    # Deduct for high average loop time
    if mean_loop > 80:
        score -= 20
    elif mean_loop > 50:
        score -= 10
    
    score = max(0, score)
    
    # Store metrics
    result.compute_stability = {
        'efficiency_score': score,
        'coefficient_variation': cv,
        'mean_loop_time': mean_loop,
        'std_loop_time': std_loop,
        'blocking_spikes': spike_count,
        'spike_percentage': spike_percentage,
        'periodic_latency': periodic_latency,
        'has_jitter': cv > 0.2
    }
    
    # Generate warnings
    if cv > 0.2:
        result.warnings.append(
            f"High algorithmic jitter detected (CV: {cv:.2f}). "
            f"Loop times vary significantly from {loop_times.min():.1f}ms to {loop_times.max():.1f}ms"
        )
    
    if spike_count > 0:
        result.warnings.append(
            f"{spike_count} blocking spikes detected ({spike_percentage:.1f}% of loops >3σ). "
            f"Max spike: {blocking_spikes.max():.1f}ms"
        )
    
    if periodic_latency:
        result.critical_issues.append(
            "Periodic latency pattern detected - suggests Java GC or background task interference"
        )
    
    if mean_loop > 50:
        result.warnings.append(
            f"Average loop time is high ({mean_loop:.1f}ms). Target <20ms for responsive control"
        )
    
    return result


def _analyze_disconnect_patterns(df: pd.DataFrame, result: DiagnosticResult) -> DiagnosticResult:
    """Analyze disconnect events"""
    disconnect_df = df[df['is_disconnect'] == True].copy()
    
    if len(disconnect_df) == 0:
        return result
    
    # Count disconnects
    disconnect_count = len(disconnect_df)
    
    # Check if disconnects are clustered (multiple in short time)
    if disconnect_count > 1:
        time_diffs = disconnect_df['datetime'].diff().dt.total_seconds()
        rapid_disconnects = (time_diffs < 5).sum()  # Within 5 seconds
        
        if rapid_disconnects > 0:
            result.critical_issues.append(
                f"CRITICAL: {disconnect_count} disconnect events detected, "
                f"{rapid_disconnects} occurring in rapid succession (<5s apart). "
                f"Indicates loose connection or failing hardware."
            )
        else:
            result.warnings.append(
                f"{disconnect_count} disconnect events detected. Check USB connections."
            )
    else:
        result.warnings.append(
            f"Single disconnect event detected at "
            f"{disconnect_df['datetime'].iloc[0].strftime('%H:%M:%S')}"
        )
    
    # Check for specific device mentions
    for _, row in disconnect_df.iterrows():
        if 'expansion hub' in row['message'].lower():
            result.critical_issues.append(
                "Expansion Hub disconnect - check REV Hub connection and cable quality"
            )
        elif 'motor controller' in row['message'].lower():
            result.critical_issues.append(
                "Motor Controller disconnect - inspect USB connection and controller power"
            )
    
    return result


def _calculate_health_score(result: DiagnosticResult) -> DiagnosticResult:
    """Calculate robot health score 0-100"""
    score = 100
    
    # Deductions
    score -= len(result.critical_issues) * 20  # -20 per critical issue
    score -= len(result.warnings) * 5         # -5 per warning
    score -= len(result.high_current_events) * 15  # -15 per high current event
    
    # Battery prediction impact
    if result.battery_prediction:
        if not result.battery_prediction['will_survive_match']:
            score -= 25
        elif result.battery_prediction['predicted_voltage_at_150s'] < 12.0:
            score -= 10
    
    # Compute efficiency impact
    if result.compute_stability:
        compute_score = result.compute_stability['efficiency_score']
        if compute_score < 50:
            score -= 15
        elif compute_score < 70:
            score -= 8
    
    result.health_score = max(0, min(100, score))  # Clamp between 0-100
    
    return result


def _generate_recommendations(result: DiagnosticResult) -> DiagnosticResult:
    """Generate pit crew recommendations"""
    # Battery recommendations
    if result.battery_prediction:
        pred = result.battery_prediction
        if not pred['will_survive_match']:
            result.recommendations.append(
                "Replace battery immediately - current battery will not last full match"
            )
        elif pred['predicted_voltage_at_150s'] < 12.0:
            result.recommendations.append(
                "Use a fresh battery for next match - current battery is marginal"
            )
    
    # High current draw recommendations
    if len(result.high_current_events) > 0:
        result.recommendations.append(
            "Investigate motor stalls or mechanical binding - high current draws detected. "
            "Check for: 1) Wheels binding on frame, 2) Gear mesh issues, "
            "3) Motors under excessive load"
        )
    
    # Disconnect recommendations
    disconnect_mentions = sum(1 for issue in result.critical_issues + result.warnings if 'disconnect' in issue.lower())
    if disconnect_mentions > 0:
        result.recommendations.append(
            "Secure all USB connections with cable strain relief. "
            "Consider replacing suspect USB cables. Ensure proper wire management."
        )
    
    # Performance recommendations
    performance_mentions = sum(1 for w in result.warnings if 'loop time' in w.lower() or 'performance' in w.lower())
    if performance_mentions > 0:
        result.recommendations.append(
            "Optimize code for performance - consider: 1) Reducing sensor polling frequency, "
            "2) Moving heavy calculations outside main loop, 3) Checking for blocking operations"
        )
    
    # Compute stability recommendations
    if result.compute_stability:
        cs = result.compute_stability
        if cs['has_jitter']:
            result.recommendations.append(
                "Review control loops for expensive calculations or synchronous I/O operations"
            )
        if cs['periodic_latency']:
            result.recommendations.append(
                "Investigate Java Garbage Collection or background telemetry overhead"
            )
        if cs['mean_loop_time'] > 50:
            result.recommendations.append(
                "Optimize OpMode logic to increase control frequency"
            )
    
    # If everything is good
    if len(result.recommendations) == 0 and result.health_score > 80:
        result.recommendations.append(
            "Robot is operating within normal parameters - no critical issues detected"
        )
    
    return result


def generate_diagnosis_summary(result: DiagnosticResult) -> str:
    """Generate human-readable summary"""
    # Determine severity level
    if result.health_score >= 80:
        severity = "HEALTHY"
    elif result.health_score >= 60:
        severity = "CAUTION"
    else:
        severity = "CRITICAL"
    
    # Build diagnosis
    diagnosis = f"""
## Diagnostic Report

**Robot Health Score: {result.health_score}/100** - {severity}

---

### Critical Findings

"""
    
    if len(result.critical_issues) > 0:
        for issue in result.critical_issues[:3]:  # Top 3 critical
            diagnosis += f"- {issue}\n"
    else:
        diagnosis += "- No critical issues detected\n"
    
    diagnosis += "\n### Pit Crew Action Items\n\n"
    
    top_recommendations = result.recommendations[:3] if len(result.recommendations) > 0 else ["No action required - robot is healthy"]
    
    for i, rec in enumerate(top_recommendations, 1):
        diagnosis += f"{i}. {rec}\n"
    
    # Add battery prediction if available
    if result.battery_prediction:
        pred = result.battery_prediction
        diagnosis += f"\n### Battery Forecast\n\n"
        diagnosis += f"- **Current Status:** {pred['current_voltage']:.2f}V at {pred['current_time']:.0f}s into operation\n"
        diagnosis += f"- **Match End Prediction:** {pred['predicted_voltage_at_150s']:.2f}V at 2:30 mark\n"
        
        if pred['will_survive_match']:
            diagnosis += f"- **Verdict:** Battery will survive full match (confidence: {pred['confidence']*100:.0f}%)\n"
        else:
            diagnosis += f"- **Verdict:** Battery may fail before match end - REPLACE NOW\n"
    
    # Add correlation findings
    if len(result.high_current_events) > 0:
        diagnosis += f"\n### High Current Draw Events Detected: {len(result.high_current_events)}\n\n"
        for event in result.high_current_events[:2]:  # Show top 2
            diagnosis += f"- **{event['timestamp'].strftime('%H:%M:%S')}:** {event['voltage_drop']:.2f}V drop "
            diagnosis += f"({event['voltage_before']:.2f}V → {event['voltage_after']:.2f}V) "
            diagnosis += f"correlated with motor issue\n"
    
    # Add compute stability metrics
    if result.compute_stability:
        cs = result.compute_stability
        diagnosis += f"\n### Computational Stability & Efficiency\n\n"
        diagnosis += f"- **Efficiency Score:** {cs['efficiency_score']:.0f}/100\n"
        diagnosis += f"- **Loop Time Stats:** {cs['mean_loop_time']:.1f}ms avg (σ={cs['std_loop_time']:.1f}ms)\n"
        diagnosis += f"- **Coefficient of Variation:** {cs['coefficient_variation']:.3f} "
        diagnosis += f"({'High Jitter' if cs['has_jitter'] else 'Stable'})\n"
        diagnosis += f"- **Blocking Spikes:** {cs['blocking_spikes']} events ({cs['spike_percentage']:.1f}% of loops)\n"
        if cs['periodic_latency']:
            diagnosis += f"- **Periodic Latency:** Yes (likely GC or background task)\n"
    
    diagnosis += "\n---\n*Analysis powered by Heuristic Intelligence Engine*\n"
    
    return diagnosis
