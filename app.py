
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.parser.log_parser import LogParser
from src.visualization.dashboard import create_dashboard
from src.utils.file_handler import save_uploaded_file, validate_log_file
from src.diagnostics.intelligence_engine import diagnose_issues, generate_diagnosis_summary
from src.utils.pdf_exporter import generate_single_match_pdf, generate_tournament_pdf
from datetime import datetime

st.set_page_config(
    page_title="FTC Log Doctor",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 5px 5px 0 0;
    }
    h1 {
        color: #1f77b4;
        font-weight: 600;
    }
    h2 {
        color: #2c3e50;
        font-weight: 500;
        margin-top: 1rem;
    }
    .dataframe {
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)


def process_single_file(log_content: str, filename: str) -> tuple:
    if not validate_log_file(log_content):
        return None, None, None
    
    parser = LogParser()
    parsed_data = parser.parse(log_content)
    
    if parsed_data.empty:
        return None, None, None
    
    diagnostic_result = diagnose_issues(parsed_data)
    
    match_metadata = {
        'match_name': filename,
        'health_score': diagnostic_result.health_score,
        'avg_loop_time': parsed_data['loop_time_ms'].mean() if parsed_data['loop_time_ms'].notna().any() else None,
        'starting_battery': parsed_data[parsed_data['battery_voltage'].notna()]['battery_voltage'].iloc[0] if parsed_data['battery_voltage'].notna().any() else None,
        'critical_issues': len(diagnostic_result.critical_issues),
        'timestamp': parsed_data['datetime'].min() if 'datetime' in parsed_data.columns else None
    }
    
    return parsed_data, diagnostic_result, match_metadata


def create_tournament_dashboard(tournament_df: pd.DataFrame, all_match_data: list):
    st.markdown("## Tournament Analysis")
    st.markdown("Track performance trends across multiple matches")
    st.markdown("---")
    
    match_data_lookup = {
        match_metadata['match_name']: (parsed_data, diagnostic_result, match_metadata)
        for parsed_data, diagnostic_result, match_metadata in all_match_data
    }
    
    tournament_df = tournament_df.sort_values('timestamp').reset_index(drop=True)
    tournament_df['match_number'] = range(1, len(tournament_df) + 1)
    
    st.subheader("Overall Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Matches",
            len(tournament_df),
            help="Number of matches analyzed"
        )
    
    with col2:
        avg_health = tournament_df['health_score'].mean()
        st.metric("Avg Health Score", f"{avg_health:.1f}")
    
    with col3:
        total_critical = tournament_df['critical_issues'].sum()
        st.metric("Total Critical Issues", int(total_critical))
    
    with col4:
        lowest_health_match = tournament_df.loc[tournament_df['health_score'].idxmin(), 'match_name']
        display_name = lowest_health_match if len(lowest_health_match) <= 20 else lowest_health_match[:20] + "..."
        st.metric("Worst Match", display_name)
    
    st.markdown("---")
    
    # Health score stuff
    st.subheader("Health Score Over Tournament")
    fig_health = px.line(
        tournament_df,
        x='match_number',
        y='health_score',
        markers=True,
        title='Robot Health Score Progression',
        labels={'match_number': 'Match Number', 'health_score': 'Health Score'}
    )
    fig_health.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="Healthy (80+)")
    fig_health.add_hline(y=50, line_dash="dash", line_color="orange", annotation_text="Fair (50)")
    fig_health.add_hline(y=30, line_dash="dash", line_color="red", annotation_text="Poor (30)")
    fig_health.update_traces(line_color='#1f77b4', line_width=3)
    fig_health.update_layout(height=400)
    st.plotly_chart(fig_health, use_container_width=True)
    
    if tournament_df['avg_loop_time'].notna().any():
        st.subheader("Average Loop Time Over Tournament")
        fig_loop = px.line(
            tournament_df,
            x='match_number',
            y='avg_loop_time',
            markers=True,
            title='Loop Time Performance Trend',
            labels={'match_number': 'Match Number', 'avg_loop_time': 'Avg Loop Time (ms)'}
        )
        fig_loop.add_hline(y=50, line_dash="dash", line_color="orange", annotation_text="Warning (50ms)")
        fig_loop.update_traces(line_color='#ff7f0e', line_width=3)
        fig_loop.update_layout(height=400)
        st.plotly_chart(fig_loop, use_container_width=True)
    
    if tournament_df['starting_battery'].notna().any():
        st.subheader("Starting Battery Voltage Over Tournament")
        fig_battery = px.line(
            tournament_df,
            x='match_number',
            y='starting_battery',
            markers=True,
            title='Battery Condition at Match Start',
            labels={'match_number': 'Match Number', 'starting_battery': 'Starting Voltage (V)'}
        )
        fig_battery.add_hline(y=13.0, line_dash="dash", line_color="green", annotation_text="Fresh Battery (13V)")
        fig_battery.add_hline(y=12.0, line_dash="dash", line_color="red", annotation_text="Low (12V)")
        fig_battery.update_traces(line_color='#2ca02c', line_width=3)
        fig_battery.update_layout(height=400)
        st.plotly_chart(fig_battery, use_container_width=True)
    
    st.subheader("Match-by-Match Breakdown")
    
    display_df = tournament_df[[
        'match_number', 'match_name', 'health_score', 
        'avg_loop_time', 'starting_battery', 'critical_issues'
    ]].copy()
    
    display_df.columns = ['Match #', 'File Name', 'Health Score', 'Avg Loop (ms)', 'Start Battery (V)', 'Critical Issues']
    
    def color_health_score(val):
        if pd.isna(val):
            return ''
        if val >= 80:
            return 'background-color: #90EE90'
        elif val >= 50:
            return 'background-color: #FFD700'
        else:
            return 'background-color: #FF6B6B'
    
    styled_df = display_df.style.map(color_health_score, subset=['Health Score'])
    st.dataframe(styled_df, use_container_width=True)
    
    problem_matches = tournament_df[tournament_df['health_score'] < 50]
    if len(problem_matches) > 0:
        st.warning(f"{len(problem_matches)} match(es) had poor health scores (<50)")
        with st.expander("View Problem Matches"):
            for _, match in problem_matches.iterrows():
                st.markdown(f"- **{match['match_name']}**: Health Score {match['health_score']}, {match['critical_issues']} critical issues")
    
    st.markdown("---")
    st.subheader("Individual Match Analysis")
    st.markdown("Select a specific match to view detailed diagnostics:")
    
    match_names = tournament_df['match_name'].tolist()
    selected_match = st.selectbox(
        "Choose a match to analyze:",
        options=match_names,
        format_func=lambda x: f"Match {match_names.index(x) + 1}: {x}"
    )
    
    parsed_data, diagnostic_result, match_metadata = match_data_lookup[selected_match]
    
    st.markdown(f"Detailed Analysis: {selected_match}")
    
    diagnosis_summary = generate_diagnosis_summary(diagnostic_result)
    st.markdown(diagnosis_summary)
    
    st.markdown("---")
    
    create_dashboard(parsed_data, diagnostic_result)


def main():
    st.set_page_config(
        page_title="FTC Log Doctor",
        page_icon="🔧",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("FTC Log Doctor")
    st.markdown("Diagnose your robot's health from log files")
    
    with st.sidebar:
        st.header("Analysis Mode")
        analysis_mode = st.radio(
            "Select Mode:",
            ["Single Match Diagnosis", "Tournament Trend Analysis"],
            help="Single Match: Analyze one log file\nTournament: Compare multiple matches"
        )
        
        st.markdown("---")
        st.header("Upload Log File(s)")
        
        if analysis_mode == "Single Match Diagnosis":
            uploaded_files = st.file_uploader(
                "Choose an Android logcat file",
                type=['txt', 'log'],
                help="Upload a text-based robot log file in Android logcat format",
                accept_multiple_files=False
            )
        
            if uploaded_files:
                uploaded_files = [uploaded_files]
        else:
            uploaded_files = st.file_uploader(
                "Choose multiple Android logcat files",
                type=['txt', 'log'],
                help="Upload multiple log files to analyze tournament trends",
                accept_multiple_files=True
            )
        
        if uploaded_files:
            st.success(f"Loaded: {len(uploaded_files)} file(s)")
    
    # Main content 
    if uploaded_files:
        try:
            if analysis_mode == "Single Match Diagnosis":
                # Single match
                uploaded_file = uploaded_files[0]
                
                with st.spinner("Parsing log file..."):
                    log_content = uploaded_file.read().decode('utf-8')
                    parsed_data, diagnostic_result, _ = process_single_file(log_content, uploaded_file.name)
                    
                    if parsed_data is None:
                        st.error("Invalid log file format or no data could be extracted.")
                        return
                    
                    st.success(f"Successfully parsed {len(parsed_data)} log entries")
                
                # Diagnosis
                with st.spinner("Running intelligent diagnostics..."):
                    diagnosis_summary = generate_diagnosis_summary(diagnostic_result)
                    st.markdown(diagnosis_summary)
                
                create_dashboard(parsed_data, diagnostic_result)
                
                with st.sidebar:
                    st.markdown("### Export Options")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        csv_data = parsed_data.to_csv(index=False)
                        st.download_button(
                            label="CSV Export",
                            data=csv_data,
                            file_name=f"parsed_{uploaded_file.name}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    
                    with col2:
                        pdf_buffer = generate_single_match_pdf(
                            uploaded_file.name,
                            parsed_data,
                            diagnostic_result
                        )
                        st.download_button(
                            label="PDF Report",
                            data=pdf_buffer,
                            file_name=f"report_{uploaded_file.name.replace('.txt', '').replace('.log', '')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
            
            else:
                # Tournament 
                st.info(f"Processing {len(uploaded_files)} match log files...")
                
                tournament_data = []
                all_match_data = []  
                progress_bar = st.progress(0)
                
                for idx, uploaded_file in enumerate(uploaded_files):
                    with st.spinner(f"Processing {uploaded_file.name}..."):
                        log_content = uploaded_file.read().decode('utf-8')
                        parsed_data, diagnostic_result, match_metadata = process_single_file(
                            log_content, uploaded_file.name
                        )
                        
                        if match_metadata:
                            tournament_data.append(match_metadata)
                            all_match_data.append((parsed_data, diagnostic_result, match_metadata))
                        else:
                            st.warning(f"Skipped {uploaded_file.name}: Invalid format or no data")
                    
                    progress_bar.progress((idx + 1) / len(uploaded_files))
                
                if len(tournament_data) > 0:
                    st.success(f"Successfully processed {len(tournament_data)}/{len(uploaded_files)} matches")
                    
                    tournament_df = pd.DataFrame(tournament_data)
                    
                    create_tournament_dashboard(tournament_df, all_match_data)
                    
                    with st.sidebar:
                        st.markdown("### Export Options")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            csv_data = tournament_df.to_csv(index=False)
                            st.download_button(
                                label="CSV Export",
                                data=csv_data,
                                file_name=f"tournament_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        
                        with col2:
                            pdf_buffer = generate_tournament_pdf(tournament_df, all_match_data)
                            st.download_button(
                                label="PDF Report",
                                data=pdf_buffer,
                                file_name=f"tournament_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                else:
                    st.error("No valid log files could be processed.")
        
        except Exception as e:
            st.error(f"Error processing log file(s): {str(e)}")
            st.exception(e)
    
    else:
        st.info("Select a mode and upload log file(s) to get started")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            Single Match Diagnosis
            Analyze a single match log file with:
            - AI-powered diagnostics
            - ML battery prediction
            - High current detection
            - Health scoring (0-100)
            - Interactive visualizations
            """)
        
        with col2:
            st.markdown("""
            Tournament Trend Analysis
            Compare multiple matches to identify:
            - Health score trends
            - Performance degradation
            - Battery condition patterns
            - Problem matches
            - Reliability trends
            """)
        
        st.markdown("---")
        st.markdown("""
        Features
        - Battery Voltage Analysis: Track voltage drops and identify power issues
        - Loop Time Monitoring: Detect performance spikes and bottlenecks
        - Disconnect Detection: Identify connection issues and device failures
        - Visual Diagnostics: Interactive charts and timeline views
        - AI-Powered Diagnostics: Event correlation and intelligent pattern detection
        - ML Battery Prediction: Predict if battery will survive full match
        
        Supported Log Format
        This tool expects Android logcat format files from FTC robot controllers.
        """)


if __name__ == "__main__":
    main()
