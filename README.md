# FTC Log Doctor: A Cross-Modal Prognostic Framework

## 🚀 The Vision: Beyond Reactive Maintenance

In high-stakes robotics, failure is often treated as an accident. **FTC Log Doctor treats failure as a predictable data signature.**

This platform moves robotics from **Reactive Repairs** to **Prognostic Health Management (PHM)**. By synthesizing asynchronous log streams, it identifies the "Silent Drifts"—mathematical deviations in power and compute—that precede catastrophic hardware failure.

---

## 🧠 Core Innovation: The Intelligence Engine

### 1. Cross-Modal Failure Synthesis

Traditional diagnostics monitor sensors in isolation. My engine implements **temporal correlation logic** to link hardware fluctuations with software execution logs.

**The Logic:** $V_{drop} > 1.0V$ within $\pm500ms$ of a `MotorTimeout` log triggers a **High-Current Draw Event**.

**The Impact:** Distinguishes between a weak battery (simple drop) and a mechanical stall (correlated drop + timeout).

### 2. Algorithmic Jitter & Determinism Analysis

Real-time systems require determinism. This tool uses the **Coefficient of Variation (CV)** ($\frac{\sigma}{\mu}$) of control loop latency to quantify "Jitter."

**Insight:** Detects non-deterministic spikes caused by Java Garbage Collection (GC) or thread-locking, ensuring stable PID control loops.

### 3. Predictive Match Survival (ML)

Using **scikit-learn**, the platform trains a **Linear Regression model** on live battery discharge curves to predict the voltage at the $t=150s$ mark.

**Prognostic:** Provides a survival probability and an $R^2$ confidence score, allowing teams to ground a robot before a brownout occurs.

### 4. Tournament-Scale Trend Analysis (Longitudinal Data)

The system supports **Batch Processing** to identify **Thermal Heat Soak**. By plotting health metrics across 10+ matches, it detects if hardware impedance is increasing due to thermal fatigue over the course of a tournament.

---

## 🛠️ Tech Stack & Engineering

- **Data Science:** Pandas (Vectorized manipulation), NumPy (Statistical analysis)
- **Machine Learning:** Scikit-learn (Linear Regression, Polynomial Features)
- **Visualization:** Plotly (Interactive Time-Series), Streamlit (UI)
- **Software Engineering:** Regex (Pattern Matching), PyTest (Unit Testing), Modular Architecture
- **PDF Generation:** ReportLab (Professional diagnostic reports)

---

## 📊 Dashboard Modules

| Tab | Function | Key Insight |
|-----|----------|-------------|
| 🧠 **AI Diagnostics** | Event Correlation | Identifies root-cause failures via multi-modal data synthesis |
| 📈 **Tournament Trends** | Longitudinal Drift | Tracks mechanical fatigue and "Heat Soak" across matches |
| ⏱️ **Loop Analysis** | Statistical Jitter | Quantifies software determinism via Coefficient of Variation |
| 🔋 **Battery Analysis** | ML Prognostics | Predicts electrochemical failure horizons |
| 🔌 **Connection Events** | Disconnect Detection | Identifies USB/hardware connection issues |

---

## 🏗️ Project Architecture

```
ftc-log-doctor/
├── src/
│   ├── diagnostics/     # The "Brain": Correlation & ML Models
│   ├── parser/          # Data Ingestion: Regex-based extraction
│   ├── visualization/   # Human-Machine Interface (HMI)
│   └── utils/           # PDF Export & File Handling
├── tests/               # Validation: Ensuring 100% logic reliability
├── data/
│   └── sample/          # Test log files with diverse scenarios
└── app.py               # Main Streamlit application
```

---

## 🚀 Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ftc-log-doctor.git
cd ftc-log-doctor

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8502`

---

## 📋 Features

### Single Match Diagnosis
- Real-time log parsing and analysis
- Health score calculation (0-100)
- Battery life prediction using ML
- Compute stability and efficiency metrics
- High current draw event detection
- Export to CSV or professional PDF report

### Tournament Trend Analysis
- Batch processing of multiple log files
- Health score trends across matches
- Loop time performance tracking
- Battery voltage progression
- Identification of problem matches
- Comprehensive tournament PDF report

### Computational Stability Analysis
- **Coefficient of Variation (CV)** for loop times
- **Blocking Spikes:** Loop times > 3σ from mean
- **Periodic Latency Detection:** GC or background task interference
- **Compute Efficiency Score:** 0-100 rating with deductions for jitter and spikes

---

## 🧪 Sample Data

The project includes 5 diverse sample log files for testing:

- `sample_log.txt` - Real FTC errors from production
- `battery_critical.txt` - Severe battery drain scenario
- `loop_spikes.txt` - Performance degradation with spikes
- `healthy_robot.txt` - Normal operation baseline
- `high_current_events.txt` - Motor stall correlation test

---

## 🏁 Impact & Scaling (The Moonshot)

While built for the **FIRST Tech Challenge**, the underlying framework is a prototype for **Generalized Edge-Diagnostic Platforms**.

By applying this "Failure DNA" identification to **Autonomous Last-Mile Delivery Fleets** or **Industrial IoT (IIoT)**, we can reduce global downtime by shifting the industry from **scheduled maintenance** to **Condition-Based Monitoring**.

### Key Differentiators

1. **Cross-Modal Synthesis:** Links disparate data streams (power + logs) temporally
2. **Prognostic vs. Diagnostic:** Predicts failures before they occur
3. **Statistical Rigor:** Uses CV, correlation windows, and ML confidence scores
4. **Scalable Architecture:** Modular design supports expansion to fleet-scale monitoring

---

## 📊 Technical Specifications

### Event Correlation Engine
- **Temporal Window:** ±500ms for battery-motor correlation
- **Voltage Threshold:** >1.0V drop considered significant
- **High Current Detection:** Bayesian correlation between voltage and timeouts

### Compute Stability Metrics
- **CV Threshold:** >0.2 indicates high jitter
- **Blocking Spike Definition:** Loop time > mean + 3σ
- **Periodic Latency:** Interval CV < 0.3 with mean interval > 5 loops

### ML Battery Prediction
- **Model:** Linear Regression (scikit-learn)
- **Feature:** Time elapsed (seconds)
- **Target:** Battery voltage
- **Prediction Horizon:** 150 seconds (full match duration)
- **Confidence Metric:** R² score

---

## 📄 License

This project is built for educational purposes as part of the FIRST Tech Challenge.

---

## 🤝 Contributing

Contributions are welcome! This framework can be extended to:
- Support additional log formats
- Implement more sophisticated ML models (LSTM, Random Forest)
- Add real-time streaming analysis
- Integrate with telemetry systems

---

**Built with precision. Engineered for resilience. Designed for the future of robotics diagnostics.**
