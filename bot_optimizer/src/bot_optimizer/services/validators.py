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


def validate_list_fields(fields, json_payload, errors):
    for field in fields:
        if field not in json_payload.keys():
            continue
        if not isinstance(json_payload.get(field), list):
            errors.append(f"'{field}' must be a list")
            
            
def validate_bool_fields(fields, json_payload, errors):
    for field in fields:
        if field not in json_payload.keys():
            continue
        if not isinstance(json_payload.get(field), bool):
            errors.append(f"'{field}' must be bool")


def apply_fields_validators(data, mandatory_fields, string_fields, numeric_fields, dict_fields, bool_fields, list_fields):
    errors = list()
    validate_empty_fields(mandatory_fields, data, errors)
    validate_string_fields(string_fields, data, errors)
    validate_numeric_fields(numeric_fields, data, errors)
    validate_dict_fields(dict_fields, data, errors)
    validate_list_fields(list_fields, data, errors)
    validate_bool_fields(bool_fields, data, errors)
    return errors


def validate(f, fields, *args, **kwargs):
    data = request.get_json()
    errors = apply_fields_validators(data, *fields)
    if errors:
        return jsonify({"error_message": errors}), 400
    return f(*args, **kwargs)


def hyperopt_validator(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        mandatory_fields = ["timeframe", 'timerange']
        string_fields = ['timeframe', 'timerange', 'exchange']
        numeric_fields = ['days']
        dict_fields = []
        bool_fields = []
        list_fields = []
        fields = [mandatory_fields, string_fields, numeric_fields, dict_fields, bool_fields, list_fields]
        return validate(f, fields, *args, **kwargs)
    return wrapper


def backtest_validator(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        mandatory_fields = ["timeframe", 'timerange']
        string_fields = ["timeframe", 'timerange', 'exchange']
        numeric_fields = []
        dict_fields = []
        bool_fields = []
        list_fields = []
        fields = [mandatory_fields, string_fields, numeric_fields, dict_fields, bool_fields, list_fields]
        return validate(f, fields, *args, **kwargs)
    return wrapper