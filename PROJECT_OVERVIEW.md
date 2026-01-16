# AI GENERATED FROM USER REPOSITORY

# FTC Log Doctor - Technical Overview

## What This Project Does

FTC Log Doctor is a **diagnostic web application** that analyzes robot log files from FIRST Tech Challenge competitions. It parses Android logcat format files, extracts critical metrics (battery voltage, loop times, connection issues), and visualizes them in an interactive dashboard to help teams quickly identify and diagnose robot problems.

### Problem It Solves
During FTC competitions, robots can fail due to:
- Battery voltage drops causing power loss
- Performance bottlenecks (slow loop times)
- USB device disconnections
- Motor controller timeouts
- **Correlated failures** (e.g., high current draw causing both battery drops AND motor timeouts)

Teams typically have to manually read through thousands of log lines to find issues. This tool automates that process with visual diagnostics **and AI-powered event correlation** that identifies root causes by analyzing patterns across multiple metrics simultaneously.

---

## Project Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Browser                              │
│                  (Streamlit Web UI)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    app.py                                    │
│              (Main Application Entry Point)                  │
│  - File upload handling                                      │
│  - Validation orchestration                                  │
│  - Dashboard rendering                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Parser    │  │    Utils    │  │Visualization│
│   Module    │  │   Module    │  │   Module    │
└─────────────┘  └─────────────┘  └─────────────┘
```

---

## How It Works - Step by Step

### 1. **File Upload & Validation** (`app.py` + `file_handler.py`)

**What happens:**
```python
# User uploads a .txt or .log file
uploaded_file = st.file_uploader("Choose an Android logcat file", type=['txt', 'log'])

# File is read and decoded
log_content = uploaded_file.read().decode('utf-8')

# Validation checks for Android logcat format
if not validate_log_file(log_content):
    st.error("Invalid log file format")
```

**Validation Logic** (`src/utils/file_handler.py`):
- Splits content into lines
- Searches for Android logcat timestamp pattern: `MM-DD HH:MM:SS.mmm`
- Checks for PID-TID pattern: `12345-67890/?`
- Checks for log level indicator: `E/`, `W/`, `I/`, `D/`, `V/`
- Must match pattern in at least one of first 10 lines

**Example of valid format:**
```
12-13 20:21:37.640 14992-14992/? E/NEW_BHD: Battery Power Supply logging Daemon start!!!!!
```

---

### 2. **Log Parsing** (`src/parser/log_parser.py`)

**Core Parsing Logic:**

The `LogParser` class uses **regular expressions** to extract structured data from unstructured log text:

```python
LOGCAT_PATTERN = r'(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\d+)[-\s](\d+)(?:/\?)?\s+([VDIWEF])[/\s]+([^:]+):\s+(.*)'
```

**Regex Breakdown:**
- `(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})` → Captures timestamp: `12-13 20:21:37.640`
- `(\d+)[-\s](\d+)` → Captures PID and TID: `14992-14992`
- `(?:/\?)?` → Optional `/` and `?` characters
- `([VDIWEF])` → Log level: E(rror), W(arning), I(nfo), D(ebug), V(erbose)
- `([^:]+)` → Tag name: `RobotCore`, `OpMode`, etc.
- `(.*)` → The actual log message

**Special Pattern Extraction:**

After parsing the basic structure, the parser looks for specific patterns in the message:

1. **Battery Voltage:**
   ```python
   BATTERY_PATTERN = r'battery.*?(\d+\.?\d*)\s*[vV]'
   # Matches: "Battery voltage: 13.2V" → extracts 13.2
   ```

2. **Loop Time:**
   ```python
   LOOP_TIME_PATTERN = r'loop.*?(\d+\.?\d*)\s*ms'
   # Matches: "Loop time: 25.5 ms" → extracts 25.5
   ```

3. **Disconnect Events:**
   ```python
   DISCONNECT_PATTERN = r'disconnect|connection\s+lost|device\s+not\s+found'
   # Matches keywords indicating device failures
   ```

**Data Structure Created:**

Each parsed line becomes a dictionary:
```python
{
    'timestamp': '12-13 20:21:37.640',
    'pid': 14992,
    'tid': 14992,
    'level': 'E',
    'tag': 'NEW_BHD',
    'message': 'Battery Power Supply logging Daemon start!!!!!',
    'battery_voltage': None,      # or float if detected
    'loop_time_ms': None,         # or float if detected
    'is_disconnect': False        # or True if disconnect keyword found
}
```

**Enrichment Process:**

After parsing all lines, the data is enriched:
```python
def _enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
    # Convert timestamp string to datetime object
    current_year = datetime.now().year
    df['datetime'] = pd.to_datetime(f"{current_year}-" + df['timestamp'])
    
    # Sort chronologically
    df = df.sort_values('datetime').reset_index(drop=True)
    
    # Add sequential ID for reference
    df['entry_id'] = range(1, len(df) + 1)
    
    return df
```

---

### 3. **AI Diagnostics & Event Correlation** (`src/diagnostics/intelligence_engine.py`)

After parsing, the **Intelligence Engine** analyzes the data to identify **root causes** by correlating events across multiple metrics.

#### **High Current Draw Detection**

**The Problem:**
When motors draw excessive current, two things happen simultaneously:
1. Battery voltage drops significantly (>1V)
2. Motor controllers timeout trying to communicate

Traditional analysis would see these as separate issues. The AI engine **correlates them**.

**How it works:**
```python
def _analyze_battery_correlation(df, result):
    # Find voltage drops > 1.0V
    battery_df['voltage_drop'] = battery_df['battery_voltage'].diff().abs()
    significant_drops = battery_df[battery_df['voltage_drop'] > 1.0]
    
    # Find motor timeout messages
    motor_issues = df[df['message'].str.contains('timeout|Motor|comm timeout', case=False)]
    
    # Correlate: Find motor issues within 500ms of battery drops
    for _, drop_row in significant_drops.iterrows():
        drop_time = drop_row['datetime']
        time_window = drop_time ± 500ms
        
        nearby_motor_issues = motor_issues[motor_issues['datetime'] in time_window]
        
        if len(nearby_motor_issues) > 0:
            # HIGH CURRENT DRAW EVENT DETECTED!
            result.high_current_events.append({
                'timestamp': drop_time,
                'voltage_drop': drop_row['voltage_drop'],
                'motor_issues': nearby_motor_issues['message'].tolist(),
                'severity': 'CRITICAL'
            })
```

**Key Insight:**
A 1.2V battery drop + motor timeout within 500ms = **High Current Draw Event** (likely mechanical binding, stalled motor, or excessive load)

---

#### **Machine Learning Battery Prediction**

**The Goal:**
Predict if the battery will last a full 2.5 minute (150 second) match based on current drain rate.

**Algorithm: Linear Regression**

```python
from sklearn.linear_model import LinearRegression

def _predict_battery_life(df, result):
    # Prepare training data
    battery_df['seconds_elapsed'] = (battery_df['datetime'] - battery_df['datetime'].iloc[0]).dt.total_seconds()
    
    X = battery_df['seconds_elapsed'].values.reshape(-1, 1)  # Time (independent variable)
    y = battery_df['battery_voltage'].values                 # Voltage (dependent variable)
    
    # Train linear regression model
    model = LinearRegression()
    model.fit(X, y)
    
    # Predict voltage at 150 seconds (2.5 min match)
    predicted_voltage = model.predict([[150]])[0]
    
    # Calculate confidence (R² score)
    confidence = model.score(X, y)
    
    result.battery_prediction = {
        'predicted_voltage_at_150s': predicted_voltage,
        'will_survive_match': predicted_voltage > 11.5,  # 11.5V critical cutoff
        'confidence': confidence
    }
```

**Example:**
- Battery readings: `[(0s, 13.2V), (5s, 13.0V), (10s, 12.8V), ...]`
- Linear regression finds: `voltage = 13.2 - 0.02 * seconds`
- Prediction at 150s: `voltage = 13.2 - 0.02 * 150 = 10.2V`
- Result: **CRITICAL** - Battery will drop below 11.5V cutoff!

**Why Linear Regression?**
- Simple and interpretable
- Works well for consistent drain rates
- R² score indicates if drain is linear (confidence metric)
- Fast training on small datasets

---

#### **Health Score Calculation**

**Formula:**
```python
health_score = 100
health_score -= len(critical_issues) * 20      # -20 per critical issue
health_score -= len(warnings) * 5              # -5 per warning  
health_score -= len(high_current_events) * 15  # -15 per high current event

if battery_prediction and not will_survive_match:
    health_score -= 25  # Major penalty for predicted battery failure

health_score = max(0, health_score)  # Clamp to 0 minimum
```

**Scoring Guide:**
- **90-100**: Excellent - Robot is healthy
- **70-89**: Good - Minor issues detected
- **50-69**: Fair - Multiple warnings, needs attention
- **30-49**: Poor - Critical issues present
- **0-29**: Critical - Robot will likely fail

---

#### **Intelligent Recommendations**

```python
def _generate_recommendations(result):
    if len(result.high_current_events) > 0:
        result.recommendations.append(
            "Check for mechanical binding or stalled motors causing high current draw"
        )
    
    if result.battery_prediction and not result.battery_prediction['will_survive_match']:
        result.recommendations.append(
            "Replace battery before match - predicted failure at 2:30 mark"
        )
    
    # ... more heuristics
```

**Output: "The Doctor's Diagnosis"**
```
🎯 Health Score: 45/100

🔴 Critical Issues:
  ⚡ High current draw detected at 20:21:40: 1.2V drop correlated with motor timeout
  🔋 CRITICAL: Battery predicted to reach 10.2V at 2:30 mark (below 11.5V cutoff)

💡 Top Recommendations:
  1. Check for mechanical binding or stalled motors
  2. Replace battery before match
  3. Inspect Motor Controller [AL00VXNM] connection
```

---

### 4. **Data Visualization** (`src/visualization/dashboard.py`)

The dashboard is organized into **5 tabs** using **Streamlit tabs**:

1. **Overview** - Key metrics and timeline
2. **Battery Analysis** - Voltage charts and drain analysis
3. **Loop Time Analysis** - Performance statistics
4. **Disconnect Events** - Connection issues timeline
5. **🧠 AI Diagnostics** - Event correlation, ML predictions, health score

#### **Metrics Section**
```python
def create_metrics_section(df: pd.DataFrame):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Log Entries", f"{len(df):,}")
    
    with col2:
        battery_readings = df['battery_voltage'].notna().sum()
        st.metric("Battery Readings", f"{battery_readings:,}")
    
    # ... more metrics
```

**How it works:**
- `st.columns(4)` creates 4 equal-width columns
- `df['battery_voltage'].notna().sum()` counts non-null values (i.e., how many battery readings were found)
- `.metric()` displays the number with automatic formatting

#### **Battery Analysis Tab**

**Step 1: Filter Data**
```python
battery_df = df[df['battery_voltage'].notna()].copy()
```
Creates a new DataFrame with only rows that have battery voltage data.

**Step 2: Create Interactive Chart (Plotly)**
```python
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=battery_df['datetime'],      # X-axis: time
    y=battery_df['battery_voltage'], # Y-axis: voltage
    mode='lines+markers',            # Show both line and dots
    line=dict(color='#00AA00', width=2),
    marker=dict(size=4)
))

# Add warning threshold line
fig.add_hline(y=12.0, line_dash="dash", line_color="red",
              annotation_text="Low Battery Warning (12V)")
```

**Step 3: Detect Voltage Drops**
```python
# Calculate change between consecutive readings
battery_df['voltage_change'] = battery_df['battery_voltage'].diff()

# Find significant drops (>0.5V)
significant_drops = battery_df[battery_df['voltage_change'] < -0.5]
```

**Pandas `.diff()` explanation:**
- Takes difference between each row and the previous row
- `[13.2, 13.0, 12.5]` → `[NaN, -0.2, -0.5]`
- Negative values = voltage drop

#### **Loop Time Analysis Tab**

**Statistical Analysis:**
```python
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
```

**Why these metrics matter:**
- **Average**: Overall performance baseline
- **Median**: More robust than average (not skewed by outliers)
- **Max**: Worst-case performance
- **95th Percentile**: Performance threshold that 95% of loops meet

**Spike Detection:**
```python
spikes = loop_df[loop_df['loop_time_ms'] > 50]
```
Simple boolean filtering: keep only rows where loop time > 50ms threshold.

#### **Disconnect Events Tab**

**Timeline Visualization:**
```python
fig.add_trace(go.Scatter(
    x=disconnect_df['datetime'],
    y=[1] * len(disconnect_df),  # All at y=1 (horizontal line)
    mode='markers',
    marker=dict(size=15, color='red', symbol='x'),
    text=disconnect_df['message'],
    hovertemplate='<b>%{text}</b><br>Time: %{x}<extra></extra>'
))
```

Creates a timeline with red X markers showing when disconnects occurred.

---

## Data Flow Diagram

```
┌─────────────────┐
│  Log File Upload │
│  (sample_log.txt)│
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────┐
│  validate_log_file()            │
│  - Check for logcat pattern     │
│  - Verify format is valid       │
└────────┬────────────────────────┘
         │ Valid ✓
         ▼
┌─────────────────────────────────┐
│  LogParser.parse()              │
│  1. Split into lines            │
│  2. Regex match each line       │
│  3. Extract: timestamp, PID,    │
│     TID, level, tag, message    │
│  4. Search for battery voltage  │
│  5. Search for loop time        │
│  6. Search for disconnect words │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Create Pandas DataFrame        │
│  Columns:                       │
│  - entry_id                     │
│  - datetime                     │
│  - level                        │
│  - tag                          │
│  - message                      │
│  - battery_voltage              │
│  - loop_time_ms                 │
│  - is_disconnect                │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  create_dashboard()             │
│  1. Calculate metrics           │
│  2. Filter data by type         │
│  3. Create Plotly charts        │
│  4. Detect anomalies            │
│  5. Render Streamlit UI         │
└─────────────────────────────────┘
```

---

## Key Technologies Explained

### **Streamlit**
- **What**: Python framework for building data apps
- **Why**: Turns Python scripts into web apps with minimal code
- **How**: 
  ```python
  st.title("My App")        # Renders as <h1>
  st.metric("Value", 100)   # Renders as metric card
  st.plotly_chart(fig)      # Renders interactive chart
  ```
- Auto-reruns script when user interacts (file upload, button click)

### **Pandas**
- **What**: Data manipulation library
- **Why**: Excel-like operations on tabular data
- **Key operations used:**
  ```python
  df[df['voltage'] < 12]    # Filter rows
  df['voltage'].mean()      # Calculate average
  df.sort_values('time')    # Sort by column
  df['change'] = df['voltage'].diff()  # Calculate differences
  ```

### **Plotly**
- **What**: Interactive charting library
- **Why**: Creates zoomable, hoverable charts that work in web browsers
- **Features used:**
  - Line charts with markers
  - Horizontal threshold lines
  - Custom hover tooltips
  - Time-series x-axis

### **Regular Expressions (Regex)**
- **What**: Pattern matching language
- **Why**: Extract structured data from unstructured text
- **Example breakdown:**
  ```python
  r'(\d{2}-\d{2})'  # Matches two digits, dash, two digits: 12-13
  r'\s+'            # Matches one or more whitespace characters
  r'[VDIWEF]'       # Matches any single character in the set
  r'.*?'            # Non-greedy match of any characters
  r'(\d+\.?\d*)'    # Matches numbers with optional decimal: 13 or 13.2
  ```

---

## Example: Tracing One Log Line Through The System

**Input Log Line:**
```
12-13 20:21:48.234 13500-14955/? W/RobotCore: Battery voltage: 11.85V - LOW BATTERY WARNING
```

**Step 1: Validation** (`file_handler.py`)
```python
# Regex matches the pattern
matches = re.search(r'\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+\d+[-\s]\d+.*?[VDIWEF][/\s]', line)
# Result: True (valid logcat format)
```

**Step 2: Parsing** (`log_parser.py`)
```python
# Main regex captures groups
match = re.match(LOGCAT_PATTERN, line)
# Groups:
# 1: '12-13 20:21:48.234'
# 2: '13500'
# 3: '14955'
# 4: 'W'
# 5: 'RobotCore'
# 6: 'Battery voltage: 11.85V - LOW BATTERY WARNING'

# Battery pattern search
battery_match = re.search(r'battery.*?(\d+\.?\d*)\s*[vV]', message)
# Group 1: '11.85'
```

**Step 3: DataFrame Row**
```python
{
    'entry_id': 42,
    'timestamp': '12-13 20:21:48.234',
    'datetime': Timestamp('2026-12-13 20:21:48.234'),
    'pid': 13500,
    'tid': 14955,
    'level': 'W',
    'tag': 'RobotCore',
    'message': 'Battery voltage: 11.85V - LOW BATTERY WARNING',
    'battery_voltage': 11.85,
    'loop_time_ms': NaN,
    'is_disconnect': False
}
```

**Step 4: Visualization**
- Appears in "Battery Analysis" tab
- Plotted as a point at (datetime, 11.85)
- Below the 12.0V warning line (shown in red zone)
- Included in battery statistics (min, max, average)

---

## Configuration (`config.py`)

All thresholds and settings are centralized:

```python
# Battery thresholds (in volts)
BATTERY_WARNING_THRESHOLD = 12.0   # Yellow alert
BATTERY_CRITICAL_THRESHOLD = 11.5  # Red alert

# Loop time thresholds (in milliseconds)
LOOP_TIME_WARNING_THRESHOLD = 50.0   # Orange line
LOOP_TIME_CRITICAL_THRESHOLD = 100.0 # Red line

# File upload settings
MAX_FILE_SIZE_MB = 50
ALLOWED_FILE_EXTENSIONS = ['.txt', '.log']
```

**Why separate config:**
- Easy to adjust thresholds without touching code
- Different teams might have different acceptable ranges
- Single source of truth for all constants

---

## Testing (`tests/test_log_parser.py`)

Unit tests ensure the parser works correctly:

```python
def test_parse_valid_logcat_line():
    parser = LogParser()
    line = "01-16 10:30:45.123  1234  5678 I RobotCore: Battery voltage: 13.2V"
    
    result = parser._parse_line(line)
    
    assert result is not None
    assert result['battery_voltage'] == 13.2
```

**Run tests:**
```bash
pytest tests/
```

---

## Performance Considerations

1. **Memory Efficient:**
   - Reads file once into memory
   - Uses pandas DataFrame for efficient column operations
   - Filters create views, not copies (`.copy()` only when needed)

2. **Parsing Speed:**
   - Regex compiled once (class-level)
   - Single-pass through file
   - Handles ~10,000 lines in < 2 seconds

3. **Visualization:**
   - Plotly renders in browser (offloads from Python)
   - Downsampling not needed for typical log sizes
   - Charts cached by Streamlit between reruns

---

## Future Enhancements

1. **Multi-File Comparison:**
   - Upload multiple logs
   - Compare performance across matches

2. **Export Reports:**
   - PDF summary with key findings
   - Automated issue detection

3. **Real-Time Monitoring:**
   - Connect to robot during match
   - Live dashboard updates

4. **Machine Learning:**
   - Predict failures before they happen
   - Anomaly detection algorithms

5. **Custom Patterns:**
   - User-defined regex patterns
   - Team-specific metrics

---

## Troubleshooting

### "Invalid log file format" error
- **Cause:** File doesn't match Android logcat pattern
- **Fix:** Ensure file has timestamp format `MM-DD HH:MM:SS.mmm` in first 10 lines

### "No data could be extracted"
- **Cause:** No battery/loop time/disconnect patterns found
- **Fix:** Check that log messages contain keywords like "battery", "voltage", "loop time", "disconnect"

### Chart not showing data
- **Cause:** All values are null for that metric
- **Fix:** Verify log file contains the specific metric being visualized

---

## Summary

**FTC Log Doctor** transforms raw robot log files into actionable insights through:

1. **Intelligent Parsing** - Regex-based extraction of structured data from unstructured logs
2. **AI-Powered Diagnostics** - Event correlation to identify root causes (e.g., high current draw = battery drop + motor timeout)
3. **Machine Learning Prediction** - Linear regression model predicts if battery will survive full match
4. **Automated Health Scoring** - 0-100 score with weighted penalties for critical issues
5. **Visual Diagnostics** - Interactive charts showing battery, performance, and connectivity issues
6. **Rapid Troubleshooting** - Identifies problems in seconds that would take minutes manually

**Tech Stack:**
- Python 3.14
- Streamlit (Web UI)
- Pandas (Data manipulation)
- Plotly (Visualization)
- scikit-learn (ML prediction)
- NumPy (Numerical computations)
- Regex (Parsing)

**Use Case:**
FTC teams can upload match logs after competitions, quickly identify why their robot failed (including correlated failures that aren't obvious), get ML-powered predictions about battery life, and receive actionable recommendations before the next match.

**Sample Logs Included:**
- `sample_log.txt` - Real FTC log with multiple errors
- `battery_critical.txt` - Severe battery drainage scenario
- `loop_spikes.txt` - Loop time issues + disconnects
- `healthy_robot.txt` - Minimal issues (tests high health score)
- `high_current_events.txt` - Battery drops + motor timeouts correlation
