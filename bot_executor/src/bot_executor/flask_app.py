import logging
import json
import traceback
from flask import Flask, request, jsonify, Response

from bot_executor.config import configure_logging
from bot_executor.services import validators
from bot_executor.services.execute import order_execute, order_clean
from bot_executor.services.auth import authenticate


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
        if authenticate(order_info) is False:
            raise Exception("access token is not valid")
        order = order_execute(order_info)
        if 'error_message' in order:
            return jsonify(order), 500
        return jsonify(order), 200
    except Exception as e:
        order_info.pop('token', None)
        logging.error(f"Order info: {order_info}")
        logging.exception("")
        traceback.format_exc()
        return jsonify({"error_message": str(e)}), 500


@app.route("/clean", methods=["POST"])
@validators.clean_validator
def clean():
    order_info = request.get_json()
    try:
        if authenticate(order_info) is False:
            raise Exception("access token is not valid")
        result = order_clean(order_info)
        return jsonify(result), 200
    except Exception as e:
        order_info.pop('token', None)
        logging.error(f"Order info: {order_info}")
        logging.exception("")
        traceback.format_exc()
        return jsonify({"error_message": str(e)}), 500


if __name__ == "__main__":
    app.run()
