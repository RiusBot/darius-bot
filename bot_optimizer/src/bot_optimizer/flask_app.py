import logging
import json
import traceback
from flask import Flask, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy

from bot_optimizer.config import configure_logging, get_db_uri
from bot_optimizer.services import validators
from bot_optimizer.services.freqtrade import freqtrade_hyperopt, freqtrade_backtest
from bot_optimizer.services.auth import authenticate


configure_logging()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = get_db_uri()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


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


@app.route("/hyperopt", methods=["POST"])
@validators.hyperopt_validator
def hyperopt():
    json_paylaod = request.get_json()
    try:
        if authenticate(json_paylaod) is False:
            raise Exception("access token is not valid")
        result = freqtrade_hyperopt(db, json_paylaod)
        return jsonify(result), 200
    except Exception as e:
        logging.info(json.dumps(json_paylaod, indent=4))
        logging.exception("")
        error = traceback.format_exc()
        error = str(e)
        return jsonify({"error_message": error}), 500


@app.route("/backtest", methods=["POST"])
@validators.backtest_validator
def backtest():
    json_paylaod = request.get_json()
    try:
        if authenticate(json_paylaod) is False:
            raise Exception("access token is not valid")
        result = freqtrade_backtest(db, json_paylaod)
        return jsonify(result), 200
    except Exception as e:
        logging.info(json.dumps(json_paylaod, indent=4))
        logging.exception("")
        error = traceback.format_exc()
        error = str(e)
        return jsonify({"error_message": error}), 500


if __name__ == "__main__":
    app.run()
