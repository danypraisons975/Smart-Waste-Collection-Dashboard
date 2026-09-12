# Smart Waste Collection Management System

A Flask-based prototype dashboard for **Project Better Tomorrow — Pathway A**. It combines household readiness data, historical collection records, and a Random Forest regression estimate to make collection timing easier to understand.

> **Prototype limitation:** The included dataset is intentionally small and is based on the project document's sample observations. The prediction is for demonstration and should not be treated as a guaranteed municipal collection time.

## Features

- Dashboard summary for total houses, waste ready, houses waiting, and predicted delay.
- Expected collection time based on the normal 08:30 AM schedule plus the model estimate.
- Household readiness table loaded from CSV.
- Historical delay chart loaded from CSV.
- Random Forest Regression model using collection timing and household readiness features.
- JSON endpoint at `/api/dashboard` for future mobile or notification integrations.
- Responsive layout suitable for desktop and mobile screens.

## Project structure

```text
smart-waste-collection-dashboard/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   ├── collection_history.csv
│   └── household_status.csv
├── services/
│   ├── __init__.py
│   └── dashboard_service.py
├── static/
│   └── css/styles.css
├── templates/
│   └── dashboard.html
└── tests/
    └── test_dashboard.py
```

## Run in VS Code

1. Install Python 3.10 or newer.
2. Open this folder in VS Code.
3. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

4. Activate it:

   **Windows PowerShell**
   ```powershell
   .venv\Scripts\Activate.ps1
   ```

   **macOS/Linux**
   ```bash
   source .venv/bin/activate
   ```

5. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

6. Start the application:

   ```bash
   python app.py
   ```

7. Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Run tests

```bash
pytest -q
```

## Updating the data

To update the dashboard, edit the two CSV files in `data/`:

- `collection_history.csv`: one row per historical day with `day`, `collection_time`, `total_houses`, and `houses_ready`.
- `household_status.csv`: one row per house with `house_id`, `status` (`Ready` or `Waiting`), and `last_updated`.

The application reloads the CSV files whenever the page is refreshed, so no database is required for this prototype.

## Publish to GitHub

```bash
git init
git add .
git commit -m "Build smart waste collection dashboard"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/smart-waste-collection-dashboard.git
git push -u origin main
```

## Suggested next steps

Collect more real observations, compare the Random Forest model with a simple baseline such as the historical average, add user validation with at least three testers, and document feedback before making stronger claims about prediction accuracy.
