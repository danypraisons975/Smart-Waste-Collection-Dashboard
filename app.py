from flask import Flask, jsonify, render_template, request

from services.dashboard_service import DataValidationError, build_dashboard_data


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def dashboard():
        try:
            dashboard_data = build_dashboard_data()
            return render_template("dashboard.html", dashboard=dashboard_data, error=None)
        except (DataValidationError, OSError, ValueError) as exc:
            return render_template("dashboard.html", dashboard=None, error=str(exc)), 503

    @app.get("/api/dashboard")
    def dashboard_api():
        try:
            return jsonify(build_dashboard_data())
        except (DataValidationError, OSError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 503

    @app.post("/api/predict")
    def prediction_api():
        payload = request.get_json(silent=True) or request.form
        try:
            if "collection_time" in payload:
                raise DataValidationError("collection_time is not accepted because actual collection time is the prediction target.")
            ready = int(str(payload.get("houses_ready", "")).strip())
            from services.dashboard_service import predict_delay

            return jsonify(predict_delay(ready))
        except (TypeError, ValueError, DataValidationError) as exc:
            return jsonify({"error": f"Please check the inputs: {exc}"}), 400
        except (OSError, RuntimeError) as exc:
            return jsonify({"error": str(exc)}), 503

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
