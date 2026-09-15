# Problem Statement — Mission Readiness AI

## 1. The Problem

Military organizations operate aircraft, ground vehicles, propulsion systems, and other mission-critical equipment where availability and reliability directly affect operational capability.

The fundamental problem is not simply that equipment can fail. The deeper problem is that decision-makers need to answer a harder question **before a mission or maintenance window**:

> **Given the equipment's current condition and telemetry, how much remaining life may be available, is its behavior abnormal, and which asset should receive maintenance attention first?**

Traditional maintenance processes commonly rely on fixed schedules, accumulated operating hours/cycles, inspection intervals, or reactive fault events. These approaches remain useful, but they do not fully exploit continuously changing equipment telemetry.

An asset can begin developing an abnormal operating pattern **between scheduled inspections**. If that change is not detected early, maintenance personnel may discover the problem only after degradation has become significant or an unexpected failure occurs.

**Mission Readiness AI** addresses this gap by combining telemetry-based anomaly detection, Remaining Useful Life (RUL) prediction, health scoring, maintenance prioritization, and an AI explanation layer. The objective is not to replace engineers or make autonomous mission decisions; it is to turn raw telemetry into **early, explainable maintenance decision support**.

## 2. Who Is Affected?

### Maintenance and Engineering Teams

These are the primary users. They need to determine which assets require attention, whether an asset's behavior is changing, how urgently an inspection should be considered, and what telemetry provides evidence for an alert. Large fleets make continuous manual evaluation of multivariate telemetry difficult.

### Fleet and Operations Managers

They need a fleet-level view: how many assets are healthy, which show elevated risk, which should be prioritized, and where maintenance capacity may be needed. Raw telemetry does not directly answer these questions.

### Mission Planners and Decision-Makers

Decision-makers need concise, interpretable information rather than hundreds of sensor values. The useful output is not a list of raw readings; it is a statement such as: **the asset has very low predicted remaining life, abnormal telemetry, and high maintenance priority.**

### The Organization

Unexpected failures can lead to reduced availability, unplanned maintenance, disrupted maintenance schedules, increased engineering workload, and reduced confidence in fleet availability. Therefore this is an **asset availability and maintenance decision problem**, not merely a sensor-analysis problem.

## 3. Why Existing Approaches Are Not Enough

Existing maintenance systems are not useless. Scheduled inspection, preventive maintenance, condition monitoring, and engineering expertise remain essential. Their limitation is that they answer different questions.

### Calendar-Based Maintenance

A schedule answers **when maintenance is planned**. It does not necessarily answer **whether the asset has started behaving abnormally since its last inspection**. Two assets with the same operating age can have different health trajectories.

### Reactive Maintenance

Reactive maintenance answers what to do after a fault occurs. The desired workflow is earlier:

```text
Telemetry change → Early detection → Risk estimation → Maintenance prioritization → Engineering inspection
```

The value is moving from reaction toward anticipation.

### Raw HUMS / Telemetry Dashboards

A dashboard can display sensor values and trends, but **visualization is not prediction**. A large fleet can generate too much multivariate information for manual evaluation to scale consistently.

Our system adds an analytical layer:

```text
Raw telemetry → Temporal features → ML models → Health indicators → Prioritized maintenance information
```

### Single-Model Solutions

RUL prediction alone does not directly answer whether the current operating pattern is unusual. Anomaly detection alone does not estimate remaining useful life. We therefore use two complementary signals:

| Signal | Question |
|---|---|
| RUL prediction | How much remaining life is estimated? |
| Anomaly detection | How unusual is the current operating pattern? |

## 4. Why This Problem Matters Now

Modern equipment is increasingly instrumented with sensors that continuously generate operational data. This creates a paradox: **organizations have more telemetry than ever, but more data does not automatically produce better maintenance decisions.**

### Increasing Data Volume

Assets generate many telemetry variables across thousands of operating cycles. Machine learning can process these multivariate patterns consistently and continuously.

### Increasing Need for Availability

Mission-critical fleets cannot treat every failure as an isolated maintenance event. Predictive maintenance shifts the objective toward using equipment condition and degradation evidence to support maintenance timing and prioritization.

### AI Can Make Predictions Actionable

Traditional ML can generate predictions, but humans still need an explanation. For example, `RUL = 1.38 cycles`, `Anomaly Severity = 80.17`, and `Mission Readiness = 8.48` are useful system outputs, but the user needs to understand why they matter. Our AI Copilot explains the already-computed ML results rather than replacing the predictive models.

## 5. Quantified Evidence Available in Our Prototype

We deliberately distinguish **benchmark evidence**, **model performance**, and **real-world operational impact**. We do not have classified or proprietary military fleet data, so we do not invent claims such as a specific percentage reduction in failures or a specific monetary saving.

### Dataset Scale

The FD001 data used in the prototype contains **20,631 training observations** and **13,096 test observations**, with multiple engine units observed over operating cycles and multiple telemetry variables per cycle.

### RUL Model Performance

We split the training data by **engine**, not individual rows, to reduce time-series leakage. The model used **80 engines for training** and **20 unseen engines for validation**, corresponding to **16,561 training observations** and **4,070 validation observations**.

| Metric | Validation result | Interpretation |
|---|---:|---|
| MAE | **23.96 cycles** | Average absolute RUL prediction error was about 24 cycles |
| RMSE | **32.57 cycles** | Larger errors receive greater penalty |
| R² | **0.7538** | About 75% of validation RUL variance was explained |

These are prototype benchmark results, not evidence of production-grade reliability.

## 6. What the System Adds

The targeted gap is a chain of decisions:

```text
Telemetry
   ↓
Is the current behavior unusual?
   ↓
Anomaly detection
   ↓
How much useful life may remain?
   ↓
RUL prediction
   ↓
How concerning is the combined condition?
   ↓
Health / readiness scoring
   ↓
What deserves engineering attention first?
   ↓
Maintenance prioritization
   ↓
Why is the system saying this?
   ↓
AI explanation
```

The contribution is connecting these layers into a single decision-support workflow.

## 7. Why RUL and Anomaly Detection Must Be Combined

RUL and anomaly detection provide different information.

An asset can have **high RUL but high anomaly severity**: its estimated remaining life may still be long, but its current behavior deserves investigation.

An asset can have **low RUL but relatively low anomaly severity**: its current pattern may not look highly unusual, while its estimated remaining life is already short.

Therefore:

> **RUL provides a degradation horizon, while anomaly detection provides a current-condition signal.**

## 8. Proposed Problem Definition

### Input

For each asset, the system receives time-series telemetry including temperature-related variables, pressure-related variables, rotational-speed variables, flow-related variables, operating settings, operating cycle, and asset identifier.

### Processing

1. Validate and preprocess telemetry.
2. Remove constant/non-informative variables.
3. Create rolling statistics over recent cycles.
4. Calculate recent sensor trends.
5. Predict RUL using Random Forest.
6. Detect abnormal patterns using Isolation Forest.
7. Convert model outputs into interpretable scores.
8. Calculate Mission Readiness.
9. Assign a prototype readiness category.
10. Calculate maintenance priority.
11. Generate a maintenance-support recommendation.
12. Use an AI Copilot to explain the result.

### Output

For each asset, the system can produce predicted RUL in cycles, RUL Score, Anomaly Severity, Anomaly Health, Mission Readiness, readiness category, maintenance priority, supporting telemetry evidence, and an AI-generated explanation.

## 9. Core Innovation

The innovation is not simply **“AI on sensor data.”** The stronger proposition is:

> **Mission Readiness AI converts continuous equipment telemetry into a layered maintenance decision-support signal that combines future-life estimation, present-condition anomaly detection, maintenance prioritization, and explainable AI.**

The system separates four questions:

| Question | System answer |
|---|---|
| How much life remains? | Predicted RUL |
| Is current behavior unusual? | Anomaly detection |
| How concerning is the combined condition? | Mission Readiness Index |
| What deserves maintenance attention first? | Maintenance Priority |

## 10. Why the Approach Is Practical

The architecture is modular:

```text
                  Asset Telemetry
                         ↓
                Feature Engineering
                         ↓
             ┌───────────┴───────────┐
             ↓                       ↓
       RUL Predictor           Anomaly Detector
       Random Forest           Isolation Forest
             ↓                       ↓
        Predicted RUL          Anomaly Severity
             ↓                       ↓
        RUL Score               Anomaly Health
             └───────────┬───────────┘
                         ↓
                Mission Readiness
                         ↓
                Maintenance Priority
                         ↓
                   AI Explanation
```

Each layer can later be improved independently: the RUL model can be replaced, anomaly detection can be recalibrated, real fleet data can replace benchmark data, component-level diagnostics can be added, maintenance history can be incorporated, and uncertainty estimates can be introduced.

## 11. Why the Problem Is Technically Difficult

Equipment degradation is **temporal, multivariate, noisy, asset-dependent, partially observable, and decision-sensitive**. Sensor values fluctuate; degradation appears over time; different assets can follow different trajectories; and telemetry does not directly reveal every physical failure mechanism.

This is why the system uses temporal feature engineering rather than treating each sensor reading as an independent static record.

## 12. What Success Looks Like

A successful system helps maintenance personnel move from:

> **“When is this asset scheduled for maintenance?”**

toward:

> **“What is the asset's current health trajectory, how much useful life does the model estimate, is its behavior abnormal, and how should maintenance attention be prioritized?”**

The desired outcome is **earlier awareness and better prioritization**, not autonomous maintenance or mission decisions.

## 13. Boundaries of the Prototype

### We do claim

- Telemetry contains useful predictive information.
- ML can estimate RUL from historical trajectories.
- Anomaly detection can identify unusual multivariate operating patterns.
- Combining these signals can create an interpretable prototype readiness index.
- The system can prioritize assets for engineering review.
- An LLM can explain ML outputs to a human user.

### We do not claim

- The system guarantees failure prediction.
- A predicted RUL of 1.38 means failure will occur exactly after 1.38 cycles.
- A sensor change proves a particular component has failed.
- The Mission Readiness score is an official military standard.
- The system can autonomously authorize or reject a mission.
- Benchmark performance automatically transfers to real military equipment.

These boundaries make the proposal technically credible rather than overstated.

## 14. Why This Is a Meaningful Hackathon Problem

The core challenge is a real engineering problem:

> **How do we turn large volumes of equipment telemetry into timely, interpretable information that helps humans identify degrading assets before unexpected failures?**

It combines time-series machine learning, predictive maintenance, anomaly detection, decision-support analytics, explainable AI, and a deployable software architecture.

The prototype demonstrates a measurable path from raw data to a maintenance decision-support workflow:

**Telemetry → degradation features → RUL → anomaly → readiness → maintenance priority → explanation.**

That is the problem Mission Readiness AI is designed to solve.
