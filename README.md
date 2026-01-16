# AI GENERATED FROM USER REPOSITORY

FTC Log Doctor: A Cross-Modal Prognostic Framework🚀 
The Vision: Beyond Reactive MaintenanceIn high-stakes robotics, failure is often treated as an accident. FTC Log Doctor treats failure as a predictable data signature.This platform moves robotics from Reactive Repairs to Prognostic Health Management (PHM). By synthesizing asynchronous log streams, it identifies the "Silent Drifts"—mathematical deviations in power and compute—that precede catastrophic hardware failure.
🧠 Core Innovation: The Intelligence Engine1. Cross-Modal Failure SynthesisTraditional diagnostics monitor sensors in isolation. My engine implements temporal correlation logic to link hardware fluctuations with software execution logs.
The Logic: drop > 1.0V within 500ms of a MotorTimeout log triggers a High-Current Draw Event.The Impact: Distinguishes between a weak battery (simple drop) and a mechanical stall (correlated drop + timeout).
2. Algorithmic Jitter & Determinism AnalysisReal-time systems require determinism. This tool uses the Coefficient of Variation (CV) of control loop latency to quantify "Jitter."
Insight: Detects non-deterministic spikes caused by Java Garbage Collection (GC) or thread-locking, ensuring stable PID control loops.
3. Predictive Match Survival (ML) Using scikit-learn, the platform trains a Linear Regression model on live battery discharge curves to predict the voltage at the t=150s mark.
Prognostic: Provides a survival probability and an confidence score, allowing teams to ground a robot before a brownout occurs.
4. Tournament-Scale Trend Analysis (Longitudinal Data)The system supports Batch Processing to identify Thermal Heat Soak. By plotting health metrics across 10+ matches, it detects if hardware impedance is increasing due to thermal fatigue over the course of a tournament.
🛠️ Tech Stack & EngineeringData Science: Pandas (Vectorized manipulation), NumPy (Statistical analysis)Machine Learning: Scikit-learn (Linear Regression, Polynomial Features)Visualization: Plotly (Interactive Time-Series), Streamlit (UI)Software Engineering: Regex (Pattern Matching), PyTest (Unit Testing), Modular Architecture📊 Dashboard ModulesTabFunctionTKS 
Insight🧠 AI DiagnosticsEvent CorrelationIdentifies root-cause failures via multi-modal data synthesis.
📈 Tournament TrendsLongitudinal DriftTracks mechanical fatigue and "Heat Soak" across matches.
⏱️ Loop AnalysisStatistical JitterQuantifies software determinism via Coefficient of Variation.
🔋 Battery AnalysisML PrognosticsPredicts electrochemical failure horizons.

🏗️ Project ArchitecturePlaintextftc-log-doctor/

🏁 Impact & Scaling (The Moonshot)While built for the FIRST Tech Challenge, the underlying framework is a prototype for Generalized Edge-Diagnostic Platforms.By applying this "Failure DNA" identification to Autonomous Last-Mile Delivery Fleets or Industrial IoT (IIoT), we can reduce global downtime by shifting the industry from scheduled maintenance to Condition-Based Monitoring.

ftc-log-doctor/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
│
├── src/                            # Source code
│   ├── __init__.py
│   ├── parser/                     # Log parsing module
│   │   ├── __init__.py
│   │   └── log_parser.py          # LogParser class with regex patterns
│   │
│   ├── diagnostics/                # AI diagnostics module
│   │   ├── __init__.py
│   │   └── intelligence_engine.py # Event correlation & ML prediction
│   │
│   ├── visualization/              # Visualization module
│   │   ├── __init__.py
│   │   └── dashboard.py           # Dashboard with 5 tabs (including AI)
│   │
│   └── utils/                      # Utility functions
│       ├── __init__.py
│       └── file_handler.py        # File validation and handling
│
├── tests/                          # Unit tests
│   ├── __init__.py
│   ├── test_log_parser.py         # LogParser tests
│   └── test_intelligence_engine.py # AI engine tests
│
├── data/                           # Data directory
│   ├── sample/                     # Sample log files with diverse scenarios
│   │   ├── sample_log.txt         # Real FTC log with multiple errors
│   │   ├── battery_critical.txt   # Severe battery drainage scenario
│   │   ├── loop_spikes.txt        # Loop time issues + disconnects
│   │   ├── healthy_robot.txt      # Minimal issues (high health score)
│   │   └── high_current_events.txt # Battery drops + motor timeouts
│   └── uploads/                    # Uploaded files (gitignored)
│
└── .venv/                          # Virtual environment (gitignored)
```

## Setup Instructions

### 1. Virtual Environment

The virtual environment has already been created. To activate it:

```bash
# On Windows
.venv\Scripts\activate

# On macOS/Linux
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## Usage

1. **Upload a log file**: Click "Browse files" in the sidebar and select your Android logcat file
2. **View diagnostics**: The dashboard will automatically parse and visualize the data
3. **Analyze health metrics** across 5 tabs:
   - **Overview**: Key metrics and timeline
   - **Battery Analysis**: Voltage trends, drops, and drain rate
   - **Loop Time Analysis**: Performance statistics and spike detection
   - **Disconnect Events**: Connection issues timeline
   - **🧠 AI Diagnostics**: Event correlation, ML predictions, health score
4. **Review AI findings**:
   - Health Score (0-100)
   - High Current Draw Events (battery drops + motor timeouts)
   - Battery life prediction for full 2.5 min match
   - Actionable recommendations
5. **Download results**: Export parsed data as CSV for further analysis

## Log Format

The application expects Android logcat format:
```
MM-DD HH:MM:SS.mmm  PID  TID LEVEL TAG: MESSAGE
```

Example:
```
01-16 10:30:45.123  1234  5678 I RobotCore: Battery voltage: 13.2V
01-16 10:30:45.150  1234  5678 D OpMode: Loop time: 25.5 ms
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/ tests/
```

### Linting

```bash
flake8 src/ tests/
```

## License

MIT License - feel free to use for your FTC team!
