# Solution Overview

## 1. Solution in One View

**Mission Readiness AI** is a predictive-maintenance decision-support system that converts equipment telemetry into an interpretable assessment of asset condition.

The core mechanism is a layered pipeline:

```text
Asset Telemetry
      ↓
Temporal Feature Engineering
      ↓
 ┌───────────────┬──────────────────┐
 ↓               ↓
RUL Prediction   Anomaly Detection
(Random Forest)  (Isolation Forest)
 ↓               ↓
Predicted RUL    Anomaly Score
 ↓               ↓
RUL Score        Anomaly Severity
 └───────┬───────┘
         ↓
   Mission Readiness
         ↓
 Maintenance Priority
         ↓
 Maintenance Recommendation
         ↓
    AI Copilot
```

The important design principle is that **each layer answers a different question** rather than forcing one model to solve the entire problem.

- RUL prediction answers: **How much useful life may remain?**
- Anomaly detection answers: **Is the current operating pattern unusual?**
- Mission Readiness answers: **What is the combined health condition?**
- Maintenance Priority answers: **Which condition deserves attention first?**
- AI Copilot answers: **How can these results be explained clearly to a human?**

The AI Copilot does not replace the ML models. It explains their already-computed outputs.

---

## 2. Core Mechanism

### 2.1 Start With Time-Series Telemetry

Each asset is represented by telemetry observed across operating cycles.

The prototype uses NASA C-MAPSS FD001 turbofan-engine simulation data, which provides multiple operating and telemetry variables for each engine cycle.

We treat these variables as **engine telemetry / HUMS-like telemetry** for the prototype. C-MAPSS itself is a simulated turbofan dataset and does not literally contain a military vibration sensor.

The system therefore does not make its decision from one sensor reading. It looks at how multiple telemetry variables behave over time.

---

## 3. Temporal Feature Engineering

Raw sensor values are often noisy. More importantly, equipment degradation is a **time-dependent process**.

A single reading such as:

```text
T30 = 1611.92
```

does not tell us enough by itself.

The useful question is:

> “How has T30 been behaving during the recent operating history of this asset?”

To capture that information, we create three types of temporal features.

### 3.1 Rolling Mean

For each retained sensor, we calculate a **10-cycle rolling mean**.

Conceptually:

\[
RollingMean_t =
\frac{x_{t-9}+x_{t-8}+\cdots+x_t}{10}
\]

with shorter windows used automatically at the beginning of an asset's history.

The rolling mean reduces the effect of short-term noise and represents the asset's recent average operating condition.

### 3.2 Rolling Standard Deviation

We also calculate the **10-cycle rolling standard deviation**.

\[
RollingStd_t =
Std(x_{t-9},...,x_t)
\]

This captures recent variability.

An asset may not show a large change in its average sensor value, but increasing variability can still indicate that its operating pattern is becoming less stable.

### 3.3 Recent Trend

For every retained sensor, we calculate the slope of a linear fit over the recent 10 cycles.

\[
x \approx mt+b
\]

where \(m\) is the trend/slope.

Interpretation:

- \(m > 0\): sensor is increasing
- \(m < 0\): sensor is decreasing
- \(m \approx 0\): little directional change

This allows the model to use **direction and rate of change**, not only absolute values.

### Why this matters

The feature-engineering stage changes the problem from:

> “What are the sensor values?”

to:

> “What is the recent operating state, variability, and trajectory of the asset?”

That is much more useful for predictive maintenance.

---

# 4. RUL Prediction

## 4.1 What RUL Means

**Remaining Useful Life (RUL)** is the model's estimate of how many operating cycles remain before the benchmark end-of-life/failure condition.

The RUL model receives the engineered telemetry features and predicts:

\[
\widehat{RUL} = f(\text{telemetry, cycle, recent behavior})
\]

The prototype uses a **Random Forest Regressor**.

---

## 4.2 Why Random Forest

Random Forest was selected because it is:

- effective for nonlinear relationships,
- able to model interactions among multiple telemetry variables,
- relatively robust to noisy data,
- straightforward to train for a hackathon prototype, and
- interpretable enough to provide feature-importance information.

It also avoids assuming that degradation follows one simple linear relationship.

Conceptually:

```text
Engineered telemetry
        ↓
   Decision Tree 1 ─┐
   Decision Tree 2  │
   Decision Tree 3  ├──→ Average prediction → Predicted RUL
        ...         │
   Decision Tree N ─┘
```

The forest averages predictions from many trees.

---

## 4.3 Preventing Time-Series Leakage

A major design decision was to split validation **by engine**, not by random rows.

We used:

- 80 engines for training
- 20 different engines for validation

Why?

Suppose cycles 1–150 of the same engine were in training and cycles 151–180 were in validation.

The model would already have seen the same engine's trajectory during training. That can produce an overly optimistic evaluation.

Instead:

```text
Training engines → model learns general patterns

Unseen validation engines → test whether those patterns generalize
```

This is a more meaningful validation setup for our prototype.

---

# 5. RUL Model Performance

On the validation engines:

| Metric | Result |
|---|---:|
| MAE | **23.96 cycles** |
| RMSE | **32.57 cycles** |
| R² | **0.7538** |

The MAE of 23.96 cycles means that the absolute RUL prediction error averaged approximately 24 cycles on this validation set.

These are benchmark results. They do not imply that the same performance will automatically transfer to real military equipment.

---

# 6. Converting Predicted RUL Into an RUL Score

The Random Forest predicts RUL in **cycles**.

For the dashboard, we also need a common 0–100 health scale.

Therefore, we normalize the predicted RUL.

The prototype uses **150 cycles as a normalization reference**:

\[
RUL\ Score =
\min\left(
\frac{Predicted\ RUL}{150}\times100,
100
\right)
\]

This means:

| Predicted RUL | RUL Score |
|---:|---:|
| 150+ cycles | 100 |
| 120 cycles | 80 |
| 90 cycles | 60 |
| 60 cycles | 40 |
| 30 cycles | 20 |
| 15 cycles | 10 |
| 1.38 cycles | 0.92 |

### Why 150?

150 is **not** a failure threshold and was not learned by the model.

It is a configurable prototype reference used only to map RUL from cycles onto a 0–100 score.

The Random Forest's actual prediction remains the RUL in cycles.

For example:

```text
Random Forest
     ↓
Predicted RUL = 1.38 cycles
     ↓
Normalization
     ↓
RUL Score = 0.92 / 100
```

In a production system, this reference should be calibrated using real fleet degradation distributions and engineering requirements.

---

# 7. Anomaly Detection

RUL alone cannot describe the complete current condition of an asset.

An asset can have substantial estimated remaining life while simultaneously developing an unusual operating pattern.

Therefore, the second ML branch asks:

> **“Does the current multivariate telemetry pattern look abnormal compared with healthy behavior?”**

We use an **Isolation Forest**.

---

## 7.1 Why Isolation Forest

Isolation Forest is appropriate for this part because anomaly detection does not require a complete set of labeled failure classes.

It learns the structure of a reference population and identifies observations that are relatively easy to isolate.

Conceptually:

```text
Normal operating region

        ● ● ●
      ● ● ● ● ●
     ● ● ● ● ● ●
      ● ● ● ●

                  X
              unusual state
```

The unusual observation is isolated with fewer partitioning steps.

Therefore:

> easier to isolate → more anomalous

---

# 8. Healthy Baseline

The dataset does not explicitly provide a simple “healthy/not healthy” label for every telemetry row.

For the prototype, we define a healthy-ish baseline using:

\[
RUL \geq 100
\]

Observations satisfying this condition are used to establish the reference operating pattern.

This is a **prototype assumption**, not a universal definition of health.

The baseline is then used to train the Isolation Forest.

---

# 9. Robust Scaling

Before anomaly detection, telemetry-derived features are scaled using **RobustScaler**.

This is useful because telemetry can contain extreme values and different sensors operate on very different numerical scales.

Robust scaling uses statistics based on the median and interquartile range, making it less sensitive to extreme observations than standard mean/std scaling.

The important backend requirement is:

> **The exact scaler fitted during training must be reused during inference.**

The backend must not fit a new scaler on incoming data.

---

# 10. Anomaly Score and Calibration

Isolation Forest produces a continuous decision score.

In our implementation:

- higher score → more normal
- lower score → more anomalous

Rather than relying only on the model's default threshold, we calibrate the boundary from the healthy baseline.

We calculate:

\[
AnomalyThreshold =
5^{th}\ percentile\ of\ healthy\ baseline\ scores
\]

Then:

\[
Anomaly =
\begin{cases}
True, & Score < AnomalyThreshold\\
False, & Score \geq AnomalyThreshold
\end{cases}
\]

This makes the anomaly boundary explicitly tied to the learned healthy reference.

---

# 11. Anomaly Severity

The raw Isolation Forest score is not naturally a 0–100 severity score.

For the dashboard, we transform it into an interpretable severity measure.

The prototype uses:

\[
AnomalySeverity =
clip\left(
\frac{HealthyMax-CurrentScore}
{HealthyMax-HealthyMin}
\times100,
0,
100
\right)
\]

Interpretation:

- low severity → operating pattern is relatively close to the healthy reference
- high severity → operating pattern is strongly displaced toward the anomalous side

This score represents **abnormality of the telemetry pattern**, not a diagnosis of a specific failed component.

---

# 12. Why We Do Not Diagnose Components

Suppose Asset 40 has:

- T30 increasing
- Ps30 increasing
- T50 increasing
- Nc increasing

The system can say:

> “These telemetry variables show recent changes associated with the detected abnormal operating pattern.”

It should **not** say:

> “The T30 increase proves component X has failed.”

The reason is that the model detects statistical relationships in telemetry. It does not have a validated physical fault-isolation model proving a particular component caused the change.

This distinction prevents the AI layer from turning statistical evidence into an unsupported engineering diagnosis.

---

# 13. Combining the Two ML Signals

At this point we have two independent signals:

```text
                    Current telemetry
                           │
              ┌────────────┴────────────┐
              ↓                         ↓
       RUL Prediction            Anomaly Detection
              ↓                         ↓
      Predicted RUL                Anomaly Score
              ↓                         ↓
         RUL Score              Anomaly Severity
```

They answer different questions.

### RUL

Looks toward the **remaining degradation horizon**.

### Anomaly

Looks at the **current operating pattern**.

This separation is one of the most important design decisions in the solution.

---

# 14. Anomaly Health

Anomaly Severity is a “badness” score:

\[
0 = low\ severity
\]

\[
100 = high\ severity
\]

For combining it with RUL health, we invert it:

\[
AnomalyHealth = 100-AnomalySeverity
\]

Therefore:

- high anomaly severity → low anomaly health
- low anomaly severity → high anomaly health

For Asset 40:

\[
AnomalySeverity = 80.17
\]

so:

\[
AnomalyHealth = 100-80.17=19.83
\]

---

# 15. Mission Readiness Index

The system now has:

1. remaining-life health, and
2. current-condition health.

We combine them into a single prototype **Mission Readiness Index**.

\[
\boxed{
MissionReadiness =
0.6(RULScore)+0.4(AnomalyHealth)
}
\]

The weights are:

- 60% RUL Score
- 40% Anomaly Health

### Why 60/40?

This is a deliberate prototype design choice.

RUL receives slightly more weight because the remaining-life estimate represents the longer-term degradation state, while anomaly health represents the current operating pattern.

The weights are configurable and would need domain calibration before real operational deployment.

---

# 16. Asset 40 Worked Example

For Asset 40 at the selected validation state:

### Step 1 — RUL

\[
PredictedRUL=1.38\ cycles
\]

### Step 2 — RUL Score

\[
RULScore =
\frac{1.38}{150}\times100
\approx0.92
\]

### Step 3 — Anomaly Severity

\[
AnomalySeverity=80.17
\]

### Step 4 — Anomaly Health

\[
AnomalyHealth=100-80.17=19.83
\]

### Step 5 — Mission Readiness

\[
MissionReadiness =
0.6(0.92)+0.4(19.83)
\]

\[
\approx8.48
\]

Therefore:

```text
Predicted RUL       = 1.38 cycles
RUL Score           = 0.92 / 100
Anomaly Severity    = 80.17 / 100
Anomaly Health      = 19.83 / 100
Mission Readiness   = 8.48 / 100
```

---

# 17. Readiness Classification

For the prototype dashboard:

| Mission Readiness | Status |
|---:|---|
| ≥ 80 | READY |
| 50–79.99 | CAUTION |
| < 50 | CRITICAL |

These are **prototype classification thresholds**, not official military readiness standards.

For Asset 40:

\[
8.48 < 50
\]

Therefore:

> **Status = CRITICAL**

---

# 18. Maintenance Priority

Mission Readiness tells us the overall condition.

However, maintenance teams also need a way to prioritize assets.

We therefore calculate a separate maintenance-priority score:

\[
\boxed{
Priority =
0.5(100-RULScore)
+
0.3(AnomalySeverity)
+
0.2(100-MissionReadiness)
}
\]

The score emphasizes:

- remaining-life concern: 50%
- anomaly severity: 30%
- overall readiness concern: 20%

Higher score means higher maintenance priority.

Prototype levels:

| Priority Score | Level |
|---:|---|
| ≥ 80 | HIGH |
| 50–79.99 | MEDIUM |
| < 50 | LOW |

For Asset 40:

\[
Priority\approx91.9
\]

Therefore:

> **Maintenance Priority = HIGH**

---

# 19. Maintenance Recommendation

The recommendation layer is intentionally simple and deterministic.

It converts model outputs into a maintenance-support action.

### HIGH

If:

\[
PredictedRUL <20
\]

**OR**

\[
AnomalySeverity \ge75
\]

then:

> **Prioritize maintenance inspection and engineering review.**

### MEDIUM

If:

\[
PredictedRUL <60
\]

**OR**

\[
AnomalySeverity \ge40
\]

then:

> **Schedule maintenance inspection and continue monitoring telemetry.**

### LOW

Otherwise:

> **Continue routine monitoring and scheduled maintenance.**

The recommendation is not an autonomous operational command.

---

# 20. AI Copilot

The AI Copilot is the final explanation layer.

A key design decision is:

> **Gemini does not calculate the ML result.**

The numerical pipeline remains deterministic and model-driven:

```text
Telemetry
   ↓
ML models
   ↓
Structured health report
   ↓
Gemini
   ↓
Natural-language explanation
```

Gemini receives:

- asset ID,
- current cycle,
- predicted RUL,
- RUL Score,
- anomaly severity,
- Mission Readiness,
- readiness status,
- maintenance priority,
- recommendation,
- selected telemetry evidence.

It then explains those values in a concise format:

```text
ASSESSMENT
KEY EVIDENCE
RECOMMENDED ACTION
```

The Copilot is constrained not to:

- invent sensor values,
- change the predicted RUL,
- override the readiness classification,
- claim a component failure without evidence,
- or make autonomous mission/deployment decisions.

This separation is important because the LLM is being used for **interpretability**, not as an uncontrolled decision-maker.

---

# 21. What Makes the Solution Different From Naive Alternatives

## Naive Alternative 1: Display the sensors

A naive system could simply display:

```text
T30
T50
Ps30
P30
Nc
...
```

The user still has to interpret the telemetry.

### Our approach

We transform the telemetry into:

```text
Recent operating behavior
        ↓
RUL prediction
        ↓
Anomaly detection
        ↓
Health scores
        ↓
Maintenance priority
```

---

## Naive Alternative 2: Use only RUL

RUL tells us how much life the model estimates remains.

It does not directly tell us whether the current telemetry pattern is unusual.

### Our approach

Use both:

\[
RUL + Anomaly
\]

This provides complementary evidence.

---

## Naive Alternative 3: Use only anomaly detection

An anomaly detector can tell us:

> “Something looks unusual.”

But unusual does not automatically mean imminent failure.

### Our approach

Combine abnormality with an explicit remaining-life estimate.

---

## Naive Alternative 4: Use one giant AI/LLM prompt

A naive implementation might send raw telemetry to an LLM and ask:

> “Is this equipment safe?”

That creates serious problems:

- poor numerical reliability,
- unsupported diagnoses,
- difficult validation,
- unpredictable outputs, and
- unclear separation between evidence and interpretation.

### Our approach

Use specialized ML models for quantitative tasks and use the LLM only for explanation.

```text
ML → numbers
Rules → decision-support scores
LLM → explanation
```

This makes the system easier to test and reason about.

---

# 22. Key Design Decisions

| Decision | Why |
|---|---|
| Remove constant sensors | They provide no useful variation |
| Use rolling mean | Reduce noise and capture recent condition |
| Use rolling std | Capture recent variability |
| Use trend/slope | Capture direction of degradation |
| Split validation by engine | Reduce time-series leakage |
| Random Forest for RUL | Handles nonlinear multivariate relationships and is practical for prototype development |
| Isolation Forest for anomalies | Does not require complete fault-class labels |
| Healthy baseline RUL ≥ 100 | Provides a simple reference population for the prototype |
| RobustScaler | Reduces sensitivity to extreme telemetry values |
| 5th-percentile anomaly calibration | Defines abnormality relative to healthy behavior |
| Normalize RUL to 0–100 | Makes RUL compatible with other dashboard health scores |
| 60/40 readiness weighting | Gives slightly more influence to remaining life while retaining current-condition information |
| Separate maintenance priority | Readiness and maintenance urgency are related but not identical |
| Rule-based recommendations | Deterministic, transparent, and easy to validate |
| Gemini after ML | Adds explanation without allowing an LLM to determine numerical health |
| Engine-level validation split | Tests whether learned patterns generalize to unseen assets |

---

# 23. User Experience

The intended user experience is not a user manually interpreting machine-learning outputs.

The user should see a **fleet-level health picture first**, then drill into individual assets.

### Fleet View

The dashboard should allow the user to identify:

- assets in READY condition,
- assets requiring CAUTION,
- CRITICAL assets,
- maintenance-priority ranking, and
- the most important health indicators.

### Asset View

When an asset is selected, the user should see:

```text
Asset 40

Mission Readiness
8.48 / 100
CRITICAL

Predicted RUL
1.38 cycles

Anomaly Severity
80.17 / 100

Maintenance Priority
91.90 / 100
HIGH
```

The user can then inspect supporting telemetry trends.

### Explanation

The Copilot provides a concise explanation such as:

> The asset has very low predicted remaining life and a high anomaly severity. Recent telemetry shows coordinated changes in several monitored variables, contributing to the detected abnormal operating pattern.

The user therefore moves from:

**fleet → asset → evidence → explanation → maintenance attention**

rather than manually interpreting hundreds of raw sensor readings.

---

# 24. End-to-End Example: Asset 40

The complete reasoning chain is:

```text
Asset 40 telemetry
       ↓
10-cycle rolling statistics + trends
       ↓
Random Forest
       ↓
Predicted RUL = 1.38 cycles
       ↓
RUL Score = 0.92
       │
       ├──────────────────────┐
       ↓                      ↓
Isolation Forest        Recent telemetry
       ↓                      ↓
Anomaly Severity = 80.17   Sensor evidence
       ↓
Anomaly Health = 19.83
       ↓
Mission Readiness
= 0.6(0.92) + 0.4(19.83)
       ↓
8.48 / 100
       ↓
CRITICAL
       ↓
Maintenance Priority
≈ 91.9 / 100
       ↓
HIGH
       ↓
Maintenance inspection
and engineering review
       ↓
Gemini Copilot
       ↓
Human-readable explanation
```

This is the complete mechanism of Mission Readiness AI.

---

# 25. Important Implementation Principle

The backend must reproduce the **same inference pipeline used during model development**.

In particular, it must use:

- the same retained sensors,
- the same feature definitions,
- the same 10-cycle rolling windows,
- the same trend calculation,
- the saved anomaly scaler,
- the saved RUL model,
- the saved anomaly model,
- the same RUL normalization reference,
- the same anomaly-severity transformation,
- the same Mission Readiness formula, and
- the same classification/priority rules.

A new scaler must not be fitted on incoming production/demo data.

The goal is:

> **Same telemetry → same preprocessing → same model → same scores → same dashboard result.**

---

# 26. Final Solution Proposition

Mission Readiness AI is designed to close the gap between **raw telemetry and maintenance action**.

It does this by separating the problem into measurable layers:

**1. Understand recent behavior**  
Temporal feature engineering captures recent average condition, variability, and trends.

**2. Estimate future life**  
Random Forest predicts Remaining Useful Life.

**3. Detect present abnormality**  
Isolation Forest compares current multivariate behavior against a healthy baseline.

**4. Make the outputs interpretable**  
RUL is normalized to a 0–100 RUL Score and anomaly behavior is converted into Anomaly Severity.

**5. Combine complementary evidence**  
RUL Score and Anomaly Health produce the Mission Readiness Index.

**6. Prioritize maintenance**  
A separate maintenance-priority score identifies conditions requiring greater attention.

**7. Explain the result**  
Gemini converts the structured ML assessment into a concise human-readable explanation without changing the underlying model outputs.

The result is not simply an AI dashboard.

It is a structured decision-support pipeline:

> **Telemetry → temporal evidence → prediction → anomaly detection → readiness assessment → maintenance prioritization → explainable AI.**

This architecture makes the system useful because it connects **what the equipment is doing now**, **what its estimated remaining life is**, and **what deserves maintenance attention**, while keeping the quantitative predictions separate from the natural-language explanation.
