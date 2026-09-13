# Smart Waste Collection Management System

A Flask-based academic dashboard for understanding household waste readiness and estimating collection delay. The project addresses a practical situation in which a truck that previously arrived around 08:30 may arrive irregularly, while residents need to decide when to place waste outside.

> **Scope statement:** This application is a dataset-based demonstration. It does not receive municipal truck GPS telemetry, does not make operational collection promises, and does not claim deployment or field-test accuracy.

## Problem and proposed solution

Twelve monitored houses may prepare waste at different times. When waste is left outside for too long, animals can scatter it, while residents who leave home early may miss the collection. The dashboard summarizes household readiness, displays recorded collection history, and uses a Random Forest regression model to estimate a possible delay for a selected readiness scenario.

## Features

The dashboard provides an overview of total, ready, and waiting houses; an estimated collection time; a delay/status category; an actual historical delay chart; a household-status table; a prediction form; a JSON dashboard endpoint; validation errors for missing or malformed data; and an honest model-evaluation panel when the data size permits it.

## Technology stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, Flask |
| Data processing | pandas |
| Machine learning | scikit-learn RandomForestRegressor |
| Frontend | Jinja2 templates, semantic HTML, CSS, small vanilla JavaScript module |
| Storage | CSV files |
| Testing | pytest and Flask test client |

## Architecture

The browser requests `/`, which loads the CSV files through `services/dashboard_service.py`. The service validates and transforms the data, trains the Random Forest model, computes the dashboard payload, and renders `templates/dashboard.html`. The same service powers `/api/dashboard` and `/api/predict`. No database or external telemetry service is required.

## Dataset and provenance

The original `data/collection_history.csv` contains **12 supplied observations** labelled D1–D12. It is shown in the interface as **FIELD DATA — 12 supplied observations**. It records collection time, total houses, and houses ready. One collection time is missing, so **11 records have a usable observed delay**. `data/household_status.csv` contains the current supplied status of 12 houses.

`data/demo_collection_history.csv` contains exactly 31 reproducible synthetic rows created by `scripts/generate_demo_data.py`. The generator does not overwrite the original field file. These rows are shown in the interface as **DEMO DATA — 31 synthetic observations** and are for demonstration only and must not be described as field observations. To use them locally, set the environment variable `SWC_DATA_MODE=demo` before starting Flask. The default mode is the supplied field-tested observation file.

## Machine-learning methodology

The target is `delay_minutes = actual_collection_time - 08:30`. The supplied dataset has a constant total of 12 houses, so houses waiting and readiness ratio are deterministic transformations of houses ready. To avoid presenting redundant columns as independent evidence, the final Random Forest uses `houses_ready` as its single independent model feature. Waiting houses and readiness ratio remain useful displayed context. Actual collection time and actual delay are never used as prediction inputs. Training uses `X = houses_ready` and `y = observed delay minutes`. Prediction uses the current user-provided readiness scenario. The Random Forest uses 200 trees and a fixed random seed for reproducibility. When there are at least ten usable observations, the service reports Random Forest MAE, RMSE, and R² using a chronological hold-out split: the first eight usable observations train the model and the final three test it. It compares Random Forest MAE with a historical-average-delay baseline calculated from the training period only and applied to the same future test rows. With the original 11 usable records, the evaluation is exploratory rather than evidence of strong accuracy. The dashboard always separates historical actual delay from the current model prediction.

## Installation and running

From the project root:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install and run:

```bash
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`. For the synthetic demonstration dataset:

```powershell
$env:SWC_DATA_MODE="demo"; python app.py
```

```bash
SWC_DATA_MODE=demo python app.py
```

## API examples

`GET /api/dashboard` returns the complete dashboard payload. `POST /api/predict` accepts pre-collection JSON such as `{"houses_ready": 9}` and returns predicted delay, estimated collection time based on the normal 08:30 schedule, status, inputs, and a plain-language explanation. The endpoint deliberately does not accept actual collection time because that is the value being estimated.

## Testing

Run the automated tests with:

```bash
pytest -q
```

The suite covers page loading, dashboard JSON, the prediction endpoint, invalid inputs, and model metadata. Manual smoke checks should also include opening the page, submitting the prediction form, refreshing the dashboard, and running with `SWC_DATA_MODE=demo`.

## Project structure

```text
.
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── collection_history.csv
│   ├── household_status.csv
│   └── demo_collection_history.csv
├── scripts/generate_demo_data.py
├── services/dashboard_service.py
├── static/css/styles.css
├── templates/dashboard.html
└── test_dashboard.py
```

## Field testing, limitations, and future work

The project context describes field testing with 12 houses, and the supplied CSV files are retained as the original observations. This repository does not include a separate field-test report, accuracy study, user study, or live vehicle feed; therefore no such results are claimed here. The main limitations are the small original dataset, one missing collection time, the absence of weather/traffic/route features, and the lack of live telemetry. Future improvements should collect more real observations, define a time-based evaluation protocol, compare against a historical-average baseline, add authenticated operational users, and integrate a real telemetry source only after its data quality and permissions are established.

## Presentation readiness

The project is suitable for a faculty demonstration of a Flask dashboard, CSV data pipeline, validation behavior, and an explicitly limited Random Forest experiment. It should be presented as an academic prototype rather than a production municipal system. The most important presentation note is to distinguish the 12 supplied observations from the 31 synthetic demonstration rows.
