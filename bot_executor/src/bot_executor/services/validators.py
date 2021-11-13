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
            errors.append(f"'{field}' must be a number")


def apply_fields_validators(data, mandatory_fields, string_fields, numeric_fields, dict_fields, bool_fields):
    errors = list()
    validate_empty_fields(mandatory_fields, data, errors)
    validate_string_fields(string_fields, data, errors)
    validate_numeric_fields(numeric_fields, data, errors)
    validate_dict_fields(dict_fields, data, errors)
    validate_dict_fields(bool_fields, data, errors)
    return errors


def main_validator(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        mandatory_fields = [
            "exchange",
            "symbol",
            "action",
            "test",
            "quantity",
            "price",
            "leverage",
            "order_type",
            "stop_loss_type",
            "take_profit_type",
            "margin",
            "duplicate",
        ]
        string_fields = ["exchange", "symbol", "action", "order_type", "stop_loss_type", "tale_profit_type"]
        numeric_fields = ["quantity", "price", "leverage", "margin"]
        dict_fields = []
        bool_fields = ["test", "duplicate"]
        data = request.get_json()

        errors = apply_fields_validators(data, mandatory_fields, string_fields, numeric_fields, dict_fields, bool_fields)

        if errors:
            return jsonify({"error_messages": errors}), 400
        return f(*args, **kwargs)

    return wrapper
