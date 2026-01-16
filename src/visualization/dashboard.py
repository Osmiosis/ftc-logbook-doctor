
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
import numpy as np


def create_dashboard(df: pd.DataFrame, diagnostic_result=None):
    
    create_metrics_section(df, diagnostic_result)
    
    # The tabs for the views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview",
        "Battery Analysis",
        "Loop Time Analysis",
        "Disconnect Events",
        "AI Diagnostics"
    ])
    
    with tab1:
        create_overview_section(df)
    
    with tab2:
        create_battery_section(df, diagnostic_result)
    
    with tab3:
        create_loop_time_section(df)
    
    with tab4:
        create_disconnect_section(df)
    
    with tab5:
        if diagnostic_result:
            create_ai_diagnostics_section(df, diagnostic_result)
        else:
            st.info("Run diagnostics to see AI-powered insights")


def create_metrics_section(df: pd.DataFrame, diagnostic_result=None):
    st.subheader("Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_entries = len(df)
        st.metric("Total Log Entries", f"{total_entries:,}")
    
    with col2:
        battery_readings = df['battery_voltage'].notna().sum()
        st.metric("Battery Readings", f"{battery_readings:,}")
    
    with col3:
        loop_readings = df['loop_time_ms'].notna().sum()
        st.metric("Loop Time Readings", f"{loop_readings:,}")
    
    with col4:
        disconnect_count = df['is_disconnect'].sum()
        st.metric("Disconnect Events", f"{disconnect_count:,}", 
                  delta="Critical" if disconnect_count > 0 else None,
                  delta_color="inverse")
    
    # Health score stuff
    if diagnostic_result:
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            score = diagnostic_result.health_score
            if score >= 80:
                st.success(f"Robot Health: {score}/100 - Healthy")
            elif score >= 60:
                st.warning(f"Robot Health: {score}/100 - Caution")
            else:
                st.error(f"Robot Health: {score}/100 - Critical")
        
        with col2:
            if diagnostic_result.high_current_events:
                st.metric("High Current Events", len(diagnostic_result.high_current_events))
        
        with col3:
            if diagnostic_result.battery_prediction:
                pred = diagnostic_result.battery_prediction
                will_survive = pred['will_survive_match']
                st.metric("Match Survival", 
                         "Will Last" if will_survive else "May Fail",
                         delta=f"{pred['predicted_voltage_at_150s']:.2f}V @ 2:30")


def create_overview_section(df: pd.DataFrame):
    st.subheader("Log Analysis Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Log Level Distribution")
        level_counts = df['level'].value_counts()
        fig = px.pie(
            values=level_counts.values,
            names=level_counts.index,
            color_discrete_map={
                'E': '#dc3545',
                'W': '#ffc107',
                'I': '#17a2b8',
                'D': '#28a745',
                'V': '#6c757d'
            },
            hole=0.4
        )
        fig.update_layout(
            showlegend=True,
            height=350,
            margin=dict(t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Log Level Summary")
        st.write("")
        st.write("")
        for level in ['E', 'W', 'I', 'D', 'V']:
            count = level_counts.get(level, 0)
            level_name = {'E': 'Errors', 'W': 'Warnings', 'I': 'Info', 'D': 'Debug', 'V': 'Verbose'}[level]
            if level == 'E' and count > 0:
                st.metric(level_name, count, delta="Critical", delta_color="inverse")
            elif level == 'W' and count > 0:
                st.metric(level_name, count, delta="Review", delta_color="inverse")
            else:
                st.metric(level_name, count)
    
    st.markdown("---")
    st.subheader("Recent Log Entries")
    display_df = df[['entry_id', 'datetime', 'level', 'tag', 'message']].tail(15)
    st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)


def create_battery_section(df: pd.DataFrame, diagnostic_result=None):
    """Battery analysis stuff"""
    st.subheader("Battery Voltage Analysis")
    
    battery_df = df[df['battery_voltage'].notna()].copy()
    
    if battery_df.empty:
        st.warning("No battery voltage data found in the log file.")
        return
    
    # Battery voltage over time
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=battery_df['datetime'],
        y=battery_df['battery_voltage'],
        mode='lines+markers',
        name='Battery Voltage',
        line=dict(color='#00AA00', width=2),
        marker=dict(size=4)
    ))
    
    # Add prediction trendline
    if diagnostic_result and diagnostic_result.battery_prediction:
        pred = diagnostic_result.battery_prediction
        model = pred['model']
        
        time_range = np.linspace(0, 150, 100)  # 0 to 150 seconds
        voltage_pred = model.predict(time_range.reshape(-1, 1))
        
        start_time = battery_df['datetime'].iloc[0]
        pred_times = [start_time + pd.Timedelta(seconds=float(s)) for s in time_range]
        
        fig.add_trace(go.Scatter(
            x=pred_times,
            y=voltage_pred,
            mode='lines',
            name='AI Prediction (Linear Trend)',
            line=dict(color='purple', width=2, dash='dash'),
            opacity=0.7
        ))
        
        pred_150s_time = start_time + pd.Timedelta(seconds=150)
        fig.add_trace(go.Scatter(
            x=[pred_150s_time],
            y=[pred['predicted_voltage_at_150s']],
            mode='markers+text',
            name='2:30 Prediction',
            marker=dict(size=15, color='purple', symbol='star'),
            text=[f"{pred['predicted_voltage_at_150s']:.2f}V"],
            textposition="top center"
        ))
    
    fig.update_layout(
        title="Battery Voltage Trend",
        xaxis_title="Time",
        yaxis_title="Voltage (V)",
        hovermode='x unified',
        height=450,
        font=dict(size=12),
        title_font_size=16
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Details of prediction
    if diagnostic_result and diagnostic_result.battery_prediction:
        pred = diagnostic_result.battery_prediction
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Prediction Summary**")
            st.write(f"Drain Rate: {pred['drain_rate_per_second']*60:.3f}V/min")
            st.write(f"Predicted @ 2:30: {pred['predicted_voltage_at_150s']:.2f}V")
        with col2:
            st.markdown("**Status**")
            if pred['will_survive_match']:
                st.success(f"Battery will last full match (confidence: {pred['confidence']*100:.0f}%)")
            else:
                st.error(f"Battery may fail before match end")
    
    # Battery stats
    min_voltage = battery_df['battery_voltage'].min()
    max_voltage = battery_df['battery_voltage'].max()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Average Voltage", f"{battery_df['battery_voltage'].mean():.2f}V")
    with col2:
        st.metric("Min Voltage", f"{min_voltage:.2f}V")
    with col3:
        st.metric("Max Voltage", f"{max_voltage:.2f}V")
    
    # Detecting the drops in the voltage
    if len(battery_df) > 1:
        battery_df['voltage_change'] = battery_df['battery_voltage'].diff()
        significant_drops = battery_df[battery_df['voltage_change'] < -0.5]
        
        if not significant_drops.empty:
            st.warning(f"Detected {len(significant_drops)} significant voltage drops (>0.5V)")
            st.dataframe(
                significant_drops[['datetime', 'battery_voltage', 'voltage_change', 'message']],
                use_container_width=True,
                hide_index=True
            )


def create_loop_time_section(df: pd.DataFrame):
    st.subheader("Loop Time Analysis")
    
    loop_df = df[df['loop_time_ms'].notna()].copy()
    
    if loop_df.empty:
        st.warning("No loop time data found in the log file.")
        return
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=loop_df['datetime'],
        y=loop_df['loop_time_ms'],
        mode='lines+markers',
        name='Loop Time',
        line=dict(color='#4488FF', width=2),
        marker=dict(size=4)
    ))
    
    fig.add_hline(y=50, line_dash="dash", line_color="orange",
                  annotation_text="Warning (50ms)")
    fig.add_hline(y=100, line_dash="dash", line_color="red",
                  annotation_text="Critical (100ms)")
    
    fig.update_layout(
        title="Loop Time Performance",
        xaxis_title="Time",
        yaxis_title="Loop Time (ms)",
        hovermode='x unified',
        height=450,
        font=dict(size=12),
        title_font_size=16
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Loop time stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Average", f"{loop_df['loop_time_ms'].mean():.2f}ms")
    with col2:
        st.metric("Median", f"{loop_df['loop_time_ms'].median():.2f}ms")
    with col3:
        st.metric("Max", f"{loop_df['loop_time_ms'].max():.2f}ms")
    with col4:
        percentile_95 = loop_df['loop_time_ms'].quantile(0.95)
        st.metric("95th Percentile", f"{percentile_95:.2f}ms")
    
    # Detection for the spikes
    spikes = loop_df[loop_df['loop_time_ms'] > 50]
    
    if not spikes.empty:
        st.warning(f"Detected {len(spikes)} loop time spikes (>50ms)")
        st.dataframe(
            spikes[['datetime', 'loop_time_ms', 'message']],
            use_container_width=True,
            hide_index=True
        )


def create_disconnect_section(df: pd.DataFrame):
    st.subheader("Connection Events")
    
    disconnect_df = df[df['is_disconnect'] == True].copy()
    
    if disconnect_df.empty:
        st.success("No disconnect events detected")
        return
    
    st.error(f"Found {len(disconnect_df)} disconnect events")
    
    # Show them events
    st.dataframe(
        disconnect_df[['entry_id', 'datetime', 'level', 'tag', 'message']],
        use_container_width=True,
        hide_index=True
    )
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=disconnect_df['datetime'],
        y=[1] * len(disconnect_df),
        mode='markers',
        name='Disconnect Events',
        marker=dict(size=15, color='red', symbol='x'),
        text=disconnect_df['message'],
        hovertemplate='<b>%{text}</b><br>Time: %{x}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Disconnect Timeline",
        xaxis_title="Time",
        yaxis_title="",
        yaxis=dict(showticklabels=False),
        height=250,
        font=dict(size=12),
        title_font_size=16
    )
    st.plotly_chart(fig, use_container_width=True)


def create_ai_diagnostics_section(df: pd.DataFrame, diagnostic_result):
    st.subheader("Diagnostic Report")
    st.markdown("Automated analysis and intelligent event correlation")
    st.markdown("---")
    
    if len(diagnostic_result.high_current_events) > 0:
        st.markdown("#### High Current Draw Events")
        st.warning(
            f"Detected {len(diagnostic_result.high_current_events)} instances where significant "
            f"battery voltage drops occurred within 500ms of motor timeouts. "
            f"This indicates motors drawing excessive current, likely due to mechanical binding."
        )
        
        for i, event in enumerate(diagnostic_result.high_current_events, 1):
            with st.expander(f"Event {i}: {event['timestamp'].strftime('%H:%M:%S')} - Severity: {event['severity']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Voltage Drop", f"{event['voltage_drop']:.2f}V")
                    st.metric("Before", f"{event['voltage_before']:.2f}V")
                    st.metric("After", f"{event['voltage_after']:.2f}V")
                
                with col2:
                    st.markdown("Correlated Motor Issues:")
                    for msg in event['motor_issues']:
                        st.code(msg, language=None)
    else:
        st.success("No high current draw events detected - motors operating normally")
    
    st.markdown("---")
    
    # Battery prediction
    if diagnostic_result.battery_prediction:
        st.markdown("###Battery Life Prediction (Machine Learning)")
        
        pred = diagnostic_result.battery_prediction
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Current Voltage",
                f"{pred['current_voltage']:.2f}V",
                f"{pred['current_time']:.0f}s into session"
            )
        
        with col2:
            st.metric(
                "Predicted @ 2:30",
                f"{pred['predicted_voltage_at_150s']:.2f}V",
                delta="Will Survive" if pred['will_survive_match'] else "May Fail",
                delta_color="normal" if pred['will_survive_match'] else "inverse"
            )
        
        with col3:
            st.metric(
                "Drain Rate",
                f"{pred['drain_rate_per_second']*60:.3f}V/min",
                f"Model Confidence: {pred['confidence']*100:.0f}%"
            )
        
        battery_df = df[df['battery_voltage'].notna()].copy()
        battery_df['seconds_elapsed'] = (
            battery_df['datetime'] - battery_df['datetime'].iloc[0]
        ).dt.total_seconds()
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=battery_df['seconds_elapsed'],
            y=battery_df['battery_voltage'],
            mode='markers',
            name='Actual Readings',
            marker=dict(size=8, color='blue')
        ))
        
        time_range = np.linspace(0, 150, 100)
        voltage_pred = pred['model'].predict(time_range.reshape(-1, 1))
        
        fig.add_trace(go.Scatter(
            x=time_range,
            y=voltage_pred,
            mode='lines',
            name='Linear Regression Fit',
            line=dict(color='purple', width=3)
        ))
        
        fig.add_hline(y=11.5, line_dash="dash", line_color="red",
                      annotation_text="Critical Cutoff (11.5V)")
        fig.add_hline(y=12.0, line_dash="dash", line_color="orange",
                      annotation_text="Low Battery Warning (12V)")
        
        fig.add_vline(x=150, line_dash="dot", line_color="gray",
                      annotation_text="Match End (2:30)")
        
        fig.add_trace(go.Scatter(
            x=[150],
            y=[pred['predicted_voltage_at_150s']],
            mode='markers+text',
            name='2:30 Prediction',
            marker=dict(size=15, color='purple', symbol='star'),
            text=[f"{pred['predicted_voltage_at_150s']:.2f}V"],
            textposition="top center"
        ))
        
        fig.update_layout(
            title="Battery Drain Prediction using Linear Regression (scikit-learn)",
            xaxis_title="Time (seconds)",
            yaxis_title="Voltage (V)",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Yappin abt model
        with st.expander("How the AI Prediction Works"):
            st.markdown(f"""
            Machine Learning Model: Linear Regression (scikit-learn)
            
            1. Training Data: All battery voltage readings with timestamps
            2. Features: Elapsed time in seconds
            3. Target: Battery voltage
            4. Model: Linear regression fits a straight line through the data points
            5. Prediction: Extrapolates the trend to 150 seconds (match duration)
            
            Formula: `Voltage = Intercept + (Slope × Time)`
            
            - Slope: {pred['drain_rate_per_second']:.4f} V/second (negative = draining)
            - R² Score: {pred['confidence']:.2%} (how well the line fits the data)
            
            Assumption: Battery drain remains constant. Actual drain may vary with robot activity.
            """)
    
    st.markdown("---")
    
    # Compute stability section
    if diagnostic_result.compute_stability:
        st.markdown("#### Computational Stability & Efficiency")
        cs = diagnostic_result.compute_stability
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            score_color = "green" if cs['efficiency_score'] >= 70 else "orange" if cs['efficiency_score'] >= 50 else "red"
            st.metric("Efficiency Score", f"{cs['efficiency_score']}/100")
        with col2:
            loop_color = "green" if cs['mean_loop_time'] < 20 else "orange" if cs['mean_loop_time'] < 50 else "red"
            st.metric("Avg Loop Time", f"{cs['mean_loop_time']:.1f}ms")
        with col3:
            jitter_status = "High" if cs['has_jitter'] else "Stable"
            st.metric("Jitter Status", jitter_status, delta=f"CV: {cs['coefficient_variation']:.3f}")
        with col4:
            st.metric("Blocking Spikes", cs['blocking_spikes'])
        
        with st.expander("View Detailed Metrics"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Coefficient of Variation:** {cs['coefficient_variation']:.3f}")
                st.write(f"**Standard Deviation:** {cs['std_loop_time']:.1f}ms")
            with col2:
                st.write(f"**Spike Percentage:** {cs['spike_percentage']:.2f}%")
                if cs['periodic_latency']:
                    st.warning("Periodic latency detected - possible GC or background tasks")
                else:
                    st.success("No periodic latency patterns detected")
        
        st.markdown("---")
    
    # Problems that can happen
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Critical Issues")
        if len(diagnostic_result.critical_issues) > 0:
            for issue in diagnostic_result.critical_issues:
                st.error(issue)
        else:
            st.success("No critical issues detected")
    
    with col2:
        st.markdown("#### Warnings")
        if len(diagnostic_result.warnings) > 0:
            for warning in diagnostic_result.warnings:
                st.warning(warning)
        else:
            st.success("No warnings")
    
    st.markdown("---")
    st.markdown("#### Action Items")
    
    if len(diagnostic_result.recommendations) > 0:
        for i, rec in enumerate(diagnostic_result.recommendations, 1):
            st.markdown(f"**{i}.** {rec}")
    else:
        st.success("No action items - robot is operating normally")
