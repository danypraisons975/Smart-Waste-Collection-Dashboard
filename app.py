from flask import Flask, jsonify, render_template

from services.dashboard_service import build_dashboard_data


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def dashboard():
        return render_template("dashboard.html", dashboard=build_dashboard_data())

    @app.get("/api/dashboard")
    def dashboard_api():
        return jsonify(build_dashboard_data())

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
