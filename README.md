# AI GENERATED FROM USER REPOSITORY

# 🤖 FTC Log Doctor

A Python-based web application for analyzing and diagnosing FTC (FIRST Tech Challenge) robot health from Android logcat log files.

## Features

- 📊 **Battery Voltage Analysis**: Track voltage drops and identify power issues
- ⏱️ **Loop Time Monitoring**: Detect performance spikes and bottlenecks
- 🔌 **Disconnect Detection**: Identify connection issues and device failures
- 📈 **Visual Diagnostics**: Interactive charts and timeline views
- 🧠 **AI-Powered Diagnostics**: Event correlation and intelligent pattern detection
- 🤖 **ML Battery Prediction**: Machine learning model predicts if battery will survive full match
- ⚡ **High Current Detection**: Correlates battery drops with motor timeouts
- 💯 **Health Scoring**: Automated robot health score (0-100) with actionable recommendations

## Tech Stack

- **Python 3.14+**
- **Streamlit**: Web UI framework
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive visualizations
- **scikit-learn**: Machine learning for battery prediction
- **NumPy**: Numerical computations
- **Regex**: Log parsing

## Project Structure

```
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
