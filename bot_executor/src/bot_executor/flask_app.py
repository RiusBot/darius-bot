import logging
import json
import traceback
from flask import Flask, request, jsonify, Response

from bot_executor.config import configure_logging
from bot_executor.services import validators
from bot_executor.services.execute import order_execute


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
        logging.info("Order info:")
        logging.info(json.dumps(order_info, indent=4))
        order = order_execute(order_info)
        return jsonify(order_info), 200
    except Exception as e:
        logging.exception("")
        traceback.format_exc()
        return jsonify({"error_message": str(e)}), 500


if __name__ == "__main__":
    app.run()
