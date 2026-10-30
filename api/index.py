import os
from flask import Flask, request, jsonify
from hyundai_kia_connect_api import VehicleManager

app = Flask(__name__)

USERNAME = os.environ.get("KIA_USERNAME")
PASSWORD = os.environ.get("KIA_PASSWORD")
PIN = os.environ.get("KIA_PIN", "0000")
SECRET_KEY = os.environ.get("SECRET_KEY")
SAVED_TOKEN = os.environ.get("KIA_TOKEN")

def verify_key():
    req_key = request.args.get("key") or request.headers.get("Authorization")
    return req_key == SECRET_KEY

def get_manager(otp=None):
    if not USERNAME or not PASSWORD or not SECRET_KEY:
        raise ValueError("缺少必要的環境變數 (KIA_USERNAME, KIA_PASSWORD, SECRET_KEY)")
    
    vm = VehicleManager(region=3, brand=1, username=USERNAME, password=PASSWORD, pin=PIN)
    
    if otp:
        # 帶入驗證碼登入
        vm.check_and_refresh_token(otp=str(otp))
    else:
        vm.check_and_refresh_token()
    return vm

@app.route("/", methods=["GET"])
@app.route("/api", methods=["GET"])
def home():
    return jsonify({"status": "ready", "message": "Kia Connect API Ready"})

# 登入並取得 Token 的端點
@app.route("/login", methods=["GET"])
@app.route("/api/login", methods=["GET"])
def login_endpoint():
    if not verify_key():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    otp = request.args.get("otp")
    try:
        vm = get_manager(otp=otp)
        token_str = str(vm.token)
        return jsonify({
            "status": "success",
            "message": "登入成功！請複製下方 token 填入 Vercel 環境變數",
            "token": token_str
        })
    except Exception as e:
        err_msg = str(e)
        if "OTP" in err_msg or "otp" in err_msg:
            return jsonify({
                "status": "otp_required",
                "message": "需要驗證碼！Kia 已發送簡訊/Email，請在網址後加上 &otp=你的驗證碼 再試一次",
                "raw_error": err_msg
            }), 400
        return jsonify({"status": "error", "message": err_msg}), 500

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
