import base64
import os

from flask import Flask, request, jsonify, abort

app = Flask(__name__)

UPLOAD_DIR = "/tmp/mock_globus_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

fake_filesystem = set()
mock_transfers = {}

EXPECTED_CLIENT_ID = "test-client-id"
EXPECTED_CLIENT_SECRET = "test-client-secret"
EXPECTED_REFRESH_TOKEN = "test-refresh-token"
MOCK_ACCESS_TOKEN = "mock-access-token"
EXPECTED_BEARER_TOKEN = f"Bearer {MOCK_ACCESS_TOKEN}"


@app.route('/health', methods=['GET'])
def health():
    return "OK", 200


@app.route('/v2/oauth2/token', methods=['POST'])
def token():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith("Basic "):
        abort(401)
    try:
        decoded = base64.b64decode(auth_header.split()[1]).decode()
        client_id, client_secret = decoded.split(":")
    except Exception:
        abort(401)

    if client_id != EXPECTED_CLIENT_ID or client_secret != EXPECTED_CLIENT_SECRET:
        abort(401)

    grant_type = request.form.get("grant_type")
    refresh_token = request.form.get("refresh_token")

    if grant_type != "refresh_token":
        return jsonify({"error": "unsupported_grant_type"}), 400

    if refresh_token != "test-refresh-token":
        return jsonify({"error": "invalid_grant"}), 400

    return jsonify({
        "access_token": "mock-access-token",
        "refresh_token": "mock-refresh-token",
        "expires_in": 3600,
        "token_type": "Bearer"
    }), 200


@app.route('/v0.10/operation/endpoint/<endpoint_id>/mkdir', methods=['POST'])
def mkdir(endpoint_id):
    if request.headers.get("Authorization") != EXPECTED_BEARER_TOKEN:
        abort(401)
    data = request.get_json()
    if not data or "path" not in data:
        return jsonify({"error": "Missing path"}), 400

    path = data["path"]
    os.makedirs(os.path.join(UPLOAD_DIR, path.lstrip("/")), exist_ok=True)
    fake_filesystem.add(path)
    return jsonify({"code": "DirectoryCreated", "path": path}), 200


@app.route('/v0.10/operation/endpoint/<endpoint_id>/ls', methods=['GET'])
def ls(endpoint_id):
    if request.headers.get("Authorization") != EXPECTED_BEARER_TOKEN:
        abort(401)

    path = request.args.get("path")
    full_path = os.path.join(UPLOAD_DIR, path.lstrip("/"))
    if not os.path.exists(full_path):
        return jsonify({"error": f"Directory {path} not found"}), 404

    contents = []
    for name in os.listdir(full_path):
        item_path = os.path.join(full_path, name)
        if os.path.isfile(item_path):
            contents.append({
                "name": name,
                "size": os.path.getsize(item_path)
            })

    return jsonify({
        "DATA": contents
    }), 200


@app.route('/<path:full_path>', methods=['PUT'])
def upload_file(full_path):
    filepath = os.path.join(UPLOAD_DIR, full_path)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as f:
        f.write(request.data)
    return jsonify({"status": "uploaded", "filename": full_path}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
