import requests
from datetime import datetime

# =========================
# 1. 插件元数据
# =========================
PLUGIN_NAME = "testapp_plugin"
PLUGIN_TITLE = "本地测试服务器 (5001)"
PLUGIN_URL = "http://127.0.0.1:5001"
PLUGIN_DESC = "用于研究风控和本地调试的模拟服务器插件。请先运行 testapp_server.py"

# =========================
# 2. 核心签到函数
# =========================
def run(username, password):
    base_url = "http://127.0.0.1:5001"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AutoCheckinBot/1.0",
        "Content-Type": "application/json"
    }

    try:
        # --- 步骤 1: 登录 ---
        print(f"[Plugin] 正在登录: {username}")
        login_resp = requests.post(
            f"{base_url}/api/user/login",
            json={"username": username, "password": password},
            headers=headers,
            timeout=10
        )
        
        if login_resp.status_code != 200 or not login_resp.json().get("success"):
            return {
                "success": False,
                "message": f"登录失败: {login_resp.text}",
                "data": {}
            }
            
        user_id = login_resp.json()["data"]["id"]
        print(f"[Plugin] 登录成功, User ID: {user_id}")

        # --- 步骤 2: 签到 ---
        # 模拟人类思考时间 (1-3秒)，你可以调整这里来测试服务器的风控日志
        import time
        import random
        think_time = random.uniform(1, 3)
        print(f"[Plugin] 模拟人类思考等待 {think_time:.2f} 秒...")
        time.sleep(think_time)

        checkin_headers = {
            **headers,
            "New-Api-User": str(user_id) # 携带用户ID
        }

        print(f"[Plugin] 正在发送签到请求...")
        checkin_resp = requests.post(
            f"{base_url}/api/user/checkin",
            headers=checkin_headers,
            json={},
            timeout=10
        )
        
        if checkin_resp.status_code != 200 or not checkin_resp.json().get("success"):
            return {
                "success": False,
                "message": f"签到失败: {checkin_resp.json().get('message')}",
                "data": {}
            }
            
        quota = checkin_resp.json()["data"]["quota_awarded"]
        print(f"[Plugin] 签到成功，获得额度: {quota}")

        # --- 步骤 3: 返回标准结果 ---
        today = datetime.now().strftime("%Y-%m-%d")
        
        return {
            "success": True,
            "message": f"签到成功，获得 {quota} 积分",
            "data": {
                "checkin_date": today,
                "quota_awarded": quota,
                "checked_in_today": True,
                "checkin_count": 1,
                "total_checkins": 1,
                "total_quota": quota,
                "records": [
                    {"checkin_date": today, "quota_awarded": quota}
                ]
            }
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"插件异常: {str(e)}",
            "data": {}
        }