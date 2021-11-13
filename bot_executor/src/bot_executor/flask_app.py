import logging
import json
import socket
import traceback
from flask import Flask, request, jsonify, Response

from rob_worker.config import configure_logging
from rob_worker.services import validators
from rob_worker.services.rush import rush


configure_logging()
app = Flask(__name__)


@app.route("/_health", methods=["GET"])
def health_check():
    return Response(
        json.dumps({"status": "available"}),
        status=200,
        mimetype="application/json",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": 0,
        },
    )


@app.route("/", methods=["POST"])
@validators.main_validator
def main():
    order_info = request.get_json()
    try:
        order = order_execute(order_info)
        return jsonify(order), 200
    except Exception as e:
        logging.exception("")
        # traceback.format_exc()
        return jsonify({"error_message": str(e)}), 500


if __name__ == "__main__":
    app.run()
