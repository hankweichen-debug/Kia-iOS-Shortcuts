import os
import datetime
from flask import Flask, request, jsonify
from hyundai_kia_connect_api import VehicleManager
from hyundai_kia_connect_api.Token import Token

app = Flask(__name__)

USERNAME = os.environ.get("KIA_USERNAME")
PASSWORD = os.environ.get("KIA_PASSWORD")
PIN = os.environ.get("KIA_PIN", "0000")
SECRET_KEY = os.environ.get("SECRET_KEY")
ACCESS_TOKEN = os.environ.get("KIA_ACCESS_TOKEN")
DEVICE_ID = os.environ.get("KIA_DEVICE_ID")

def verify_key():
    req_key = request.args.get("key") or request.headers.get("Authorization")
    return req_key == SECRET_KEY

def get_vm_and_token():
    if not USERNAME or not PASSWORD or not SECRET_KEY:
        raise ValueError("缺少必要的環境變數")
    
    vm = VehicleManager(region=3, brand=1, username=USERNAME, password=PASSWORD, pin=PIN)
    tok = Token(
        username=USERNAME,
        password=PASSWORD,
        access_token=ACCESS_TOKEN,
        device_id=DEVICE_ID,
        valid_until=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365),
        pin=PIN
    )
    vm.token = tok
    if hasattr(vm, "api") and vm.api:
        vm.api.token = tok
    return vm, tok

@app.route("/", methods=["GET"])
@app.route("/api", methods=["GET"])
def home():
    return jsonify({"status": "ready", "message": "Kia Connect API Ready"})

@app.route("/unlock_car", methods=["GET", "POST"])
@app.route("/api/unlock_car", methods=["GET", "POST"])
def unlock_car():
    if not verify_key():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    try:
        vm, tok = get_vm_and_token()
        vehicles = vm.api.get_vehicles(tok)
        if not vehicles:
            return jsonify({"status": "error", "message": "找不到車輛"}), 404
        vehicle = vehicles[0]
        # 直接使用底層 API 解鎖，不觸發 VehicleManager 內部的 refresh
        res = vm.api.unlock(tok, vehicle)
        return jsonify({"status": "success", "action": "unlock", "response": str(res)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/lock_car", methods=["GET", "POST"])
@app.route("/api/lock_car", methods=["GET", "POST"])
def lock_car():
    if not verify_key():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    try:
        vm, tok = get_vm_and_token()
        vehicles = vm.api.get_vehicles(tok)
        if not vehicles:
            return jsonify({"status": "error", "message": "找不到車輛"}), 404
        vehicle = vehicles[0]
        # 直接使用底層 API 上鎖
        res = vm.api.lock(tok, vehicle)
        return jsonify({"status": "success", "action": "lock", "response": str(res)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

handler = app
