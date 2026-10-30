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

def get_manager():
    if not USERNAME or not PASSWORD or not SECRET_KEY:
        raise ValueError("缺少必要的環境變數")
    
    vm = VehicleManager(region=3, brand=1, username=USERNAME, password=PASSWORD, pin=PIN)
    
    if ACCESS_TOKEN:
        tok = Token(
            username=USERNAME,
            password=PASSWORD,
            access_token=ACCESS_TOKEN,
            device_id=DEVICE_ID,
            valid_until=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365),
            pin=PIN
        )
        vm.token = tok
        if hasattr(vm, "kia_uvo_api") and vm.kia_uvo_api:
            vm.kia_uvo_api.token = tok
    else:
        vm.check_and_refresh_token()
        
    return vm

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
        vm = get_manager()
        vm.update_all_vehicles_with_cached_state()
        v_id = list(vm.vehicles.keys())[0]
        vm.unlock(v_id)
        return jsonify({"status": "success", "action": "unlock", "vehicle_id": v_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/lock_car", methods=["GET", "POST"])
@app.route("/api/lock_car", methods=["GET", "POST"])
def lock_car():
    if not verify_key():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    try:
        vm = get_manager()
        vm.update_all_vehicles_with_cached_state()
        v_id = list(vm.vehicles.keys())[0]
        vm.lock(v_id)
        return jsonify({"status": "success", "action": "lock", "vehicle_id": v_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

handler = app
