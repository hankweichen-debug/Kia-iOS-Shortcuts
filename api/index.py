import os
from flask import Flask, request, jsonify
from hyundai_kia_connect_api import VehicleManager, ClimateRequestOptions
from hyundai_kia_connect_api.exceptions import AuthenticationError

app = Flask(__name__)

# Environment Variables
USERNAME = os.environ.get("KIA_USERNAME")
PASSWORD = os.environ.get("KIA_PASSWORD")
PIN = os.environ.get("KIA_PIN", "0000")
SECRET_KEY = os.environ.get("SECRET_KEY")
VEHICLE_ID = os.environ.get("VEHICLE_ID")

def get_vm():
    if not USERNAME or not PASSWORD or not SECRET_KEY:
        raise ValueError("Missing environment variables")
    # Region 3 is USA
    return VehicleManager(region=3, brand=1, username=USERNAME, password=PASSWORD, pin=PIN)

def verify_key():
    req_key = request.args.get("key") or request.headers.get("Authorization")
    if not req_key or req_key != SECRET_KEY:
        return False
    return True

@app.route("/", methods=["GET"])
@app.route("/api", methods=["GET"])
def home():
    return jsonify({"status": "ready", "message": "Kia iOS Shortcuts API is running!"})

@app.route("/unlock_car", methods=["GET", "POST"])
@app.route("/api/unlock_car", methods=["GET", "POST"])
def unlock_car():
    if not verify_key():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    try:
        vm = get_vm()
        vm.check_and_refresh_token()
        vm.update_all_vehicles_with_cached_state()
        v_id = VEHICLE_ID or list(vm.vehicles.keys())[0]
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
        vm = get_vm()
        vm.check_and_refresh_token()
        vm.update_all_vehicles_with_cached_state()
        v_id = VEHICLE_ID or list(vm.vehicles.keys())[0]
        vm.lock(v_id)
        return jsonify({"status": "success", "action": "lock", "vehicle_id": v_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Vercel WSGI entrypoint
handler = app
