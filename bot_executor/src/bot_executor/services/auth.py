import os
import json
import logging
import requests
import functools
# from firebase_admin import auth, initialize_app
# from google.cloud import secretmanager
# from bot_executor.adapters.firestore import firestore_db


# initialize_app()
# usingProjectId = os.getenv('project_id')


def fetch_access_token(audience_url):
    # set up metadata server request
    metadata_server_token_url = "http://metadata/computeMetadata/v1/instance/service-accounts/default/identity?audience="

    token_request_url = metadata_server_token_url + audience_url
    token_request_headers = {"Metadata-Flavor": "Google"}

    # fetch the token
    token_response = requests.get(token_request_url, headers=token_request_headers)
    jwt = token_response.content.decode("utf-8")

    return jwt


def check_client_access(json_payload):
    # TODO HERE
    try:
        # https://firebase.google.com/docs/auth/admin/verify-id-tokens#web
        clientUserIdToken = json_payload.get('idToken')
        if clientUserIdToken is None or clientUserIdToken == '':
            return False
        decoded_token = auth.verify_id_token(clientUserIdToken)
        if json_payload.get('oid', None) is not None and json_payload.get('oid') != decoded_token.get('organization', None):
            return False
        uid = decoded_token['uid']
        return uid is not None and uid is not None
    except Exception:
        logging.error("exception when dealing with check_client_access token")
        return False


@functools.lru_cache(maxsize=None)
def fetch_secret_token_old():
    secretsManagerClient = secretmanager.SecretManagerServiceClient()
    Secret = json.loads(
        secretsManagerClient.access_secret_version(
            f"projects/{usingProjectId}/secrets/recommendation/versions/latest"
        ).payload.data.decode('UTF-8')
    )
    Token = Secret['token']
    return Token


@functools.lru_cache(maxsize=None)
def fetch_secret_token():
    rec_config = firestore_db.get_document('configurations', 'recommendation')
    Token = rec_config.get("token")
    return Token


def check_server_access(json_payload):
    try:
        Token = fetch_secret_token()
        requestToken = json_payload.get('token')
        if not Token or not requestToken:
            return False
        return Token == requestToken
    except Exception:
        logging.error("exception when dealing with check_server_access token")
        return False


def authenticate(json_payload):
    return True
    if usingProjectId != "darius-prod":
        if check_client_access(json_payload) is False:
            if check_server_access(json_payload) is False:
                return False
    return True
