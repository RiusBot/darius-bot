import logging
from flask import request, jsonify
from functools import wraps


def validate_empty_fields(fields, json_payload, errors):
    for field in fields:
        if json_payload.get(field) is None:
            errors.append(f"'{field}' should not be empty")


def validate_string_fields(fields, json_payload, errors):
    for field in fields:
        if field not in json_payload.keys():
            continue
        if not isinstance(json_payload.get(field), str):
            errors.append(f"'{field}' must be a string")


def validate_numeric_fields(fields, json_payload, errors):
    for field in fields:
        if field not in json_payload.keys():
            continue
        if not isinstance(json_payload.get(field), (float, int)):
            errors.append(f"'{field}' must be a number")


def validate_dict_fields(fields, json_payload, errors):
    for field in fields:
        if field not in json_payload.keys():
            continue
        if not isinstance(json_payload.get(field), dict):
            errors.append(f"'{field}' must be a dict")
            
            
def validate_bool_fields(fields, json_payload, errors):
    for field in fields:
        if field not in json_payload.keys():
            continue
        if not isinstance(json_payload.get(field), bool):
            errors.append(f"'{field}' must be bool")


def apply_fields_validators(data, mandatory_fields, string_fields, numeric_fields, dict_fields, bool_fields):
    errors = list()
    validate_empty_fields(mandatory_fields, data, errors)
    validate_string_fields(string_fields, data, errors)
    validate_numeric_fields(numeric_fields, data, errors)
    validate_dict_fields(dict_fields, data, errors)
    validate_bool_fields(bool_fields, data, errors)
    return errors


def apply_enum_validators(data, enum_map: dict):
    errors = list()
    for key, enum_value in enum_map.items():
        if key in data:
            value = data[key]
            if data[key] not in enum_value:
                errors.append(f"'{key}' must be in {enum_value} but got '{value}'")
    return errors


def apply_others_validators(data):
    errors = list()
    enums_map = {
        'quote': {'USDT', 'USDC', 'BUSD', 'USD'}
    }
    for key, enum_value in enum_map.items():
        if key in data:
            value = data[key]
            if data[key] not in enum_value:
                errors.append(f"'{key}' must be in {enum_value} but got '{value}'")
    return errors


def main_validator(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        mandatory_fields = [
            "exchange",
            "symbol",
            "action",
            "test",
            "target",
            "quantity",
            "leverage",
            "order_type",
            "stop_loss_type",
            "take_profit_type",
            "duplicate",
            "api_key",
            "api_secret",
            # "scalp_entry",
            # "scalp_stop_loss",
            # "scalp_take_profit",
            # "price",
        ]
        string_fields = ["exchange", "symbol", "action", "order_type", "stop_loss_type", "tale_profit_type", "api_key", "api_secret", "target", "password"]
        numeric_fields = ["quantity", "leverage"]
        dict_fields = ["headers", "options"]
        bool_fields = ["test", "duplicate"]
        enums = {
            "target": {"SPOT", "MARGIN", "FUTURE"},
            "order_type": {"LIMIT", "MARKET"},
            "stop_loss_type": {"LIMIT", "MARKET", "TRAILING"},
            "take_profit_type": {"LIMIT", "MARKET", "TRAILING"},
            "exchange": {"binance", "ftx", "ftxus", "okx"},
            'action': {"SELL", "BUY"}
        }
        data = request.get_json()
        if data.get("headers") or data.get("options"):
            extra = {**data.get('headers', {}), **data.get('options', {})}
            logging.info(f"Extra: {extra}")

        errors = apply_fields_validators(data, mandatory_fields, string_fields, numeric_fields, dict_fields, bool_fields)
        errors += apply_enum_validators(data, enums)

        if errors:
            return jsonify({"error_message": errors}), 400
        return f(*args, **kwargs)

    return wrapper


def clean_validator(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        mandatory_fields = [
            "exchange",
            "test",
            "target",
            "quantity",
            "leverage",
            "order_type",
            "stop_loss_type",
            "take_profit_type",
            "duplicate",
            "api_key",
            "api_secret",
            "type",
            "others"
        ]
        string_fields = ["exchange", "type", "order_type", "stop_loss_type", "tale_profit_type", "api_key", "api_secret", "target"]
        numeric_fields = ["quantity", "leverage"]
        dict_fields = ["others"]
        bool_fields = ["test", "duplicate"]
        enums = {
            "target": {"SPOT", "MARGIN", "FUTURE"},
            "order_type": {"LIMIT", "MARKET"},
            "stop_loss_type": {"LIMIT", "MARKET", "TRAILING"},
            "take_profit_type": {"LIMIT", "MARKET", "TRAILING"},
            "exchange": {"binance", "ftx", "ftxus"}
        }
        data = request.get_json()

        errors = apply_fields_validators(data, mandatory_fields, string_fields, numeric_fields, dict_fields, bool_fields)
        errors += apply_enum_validators(data, enums)
        errors += apply_others_validators(data["others"])

        if errors:
            return jsonify({"error_message": errors}), 400
        return f(*args, **kwargs)

    return wrapper