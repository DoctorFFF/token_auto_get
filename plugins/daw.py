import time
import requests
from datetime import datetime


PLUGIN_NAME = "daw"
PLUGIN_TITLE = "DAW Claude"
PLUGIN_URL = "https://dawclaudecode.com"
PLUGIN_DESC = "DAW Claude 站点自动签到插件。使用前请先在官网注册账号。"


def run(username, password):
    login_url = "https://dawclaudecode.com/api/user/login?turnstile="
    checkin_url = "https://dawclaudecode.com/api/user/checkin"

    month = datetime.now().strftime("%Y-%m")
    history_url = f"https://dawclaudecode.com/api/user/checkin?month={month}"

    base_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "https://dawclaudecode.com",
        "Referer": "https://dawclaudecode.com/console/personal",
        "Cache-Control": "no-store",
        "Pragma": "no-cache",
    }

    try:
        session = requests.Session()

        login_resp = session.post(
            login_url,
            json={
                "username": username,
                "password": password
            },
            headers={
                **base_headers,
                "Content-Type": "application/json"
            },
            timeout=15
        )

        if login_resp.status_code != 200:
            return {
                "success": False,
                "message": f"登录失败，状态码：{login_resp.status_code}",
                "data": {}
            }

        login_data = login_resp.json()

        if not login_data.get("success"):
            return {
                "success": False,
                "message": login_data.get("message", "登录失败"),
                "data": {}
            }

        user_id = login_data["data"]["id"]

        api_headers = {
            **base_headers,
            "New-Api-User": str(user_id)
        }

        # 防止过快请求
        time.sleep(5)

        checkin_resp = session.post(
            checkin_url,
            headers=api_headers,
            data=b"",
            timeout=15
        )

        if checkin_resp.status_code != 200:
            return {
                "success": False,
                "message": f"签到失败，状态码：{checkin_resp.status_code}",
                "data": {}
            }

        checkin_data = checkin_resp.json()
        checkin_message = checkin_data.get("message", "")

        # 再等一下，让服务端同步历史记录
        time.sleep(3)

        history_resp = session.get(
            history_url,
            headers=api_headers,
            timeout=15
        )

        if history_resp.status_code != 200:
            return {
                "success": bool(checkin_data.get("success")),
                "message": checkin_message or "签到完成，但获取历史失败",
                "data": {}
            }

        history_data = history_resp.json()

        if not history_data.get("success"):
            return {
                "success": bool(checkin_data.get("success")),
                "message": checkin_message or "签到完成，但历史接口返回失败",
                "data": {}
            }

        history_body = history_data.get("data", {})
        stats = history_body.get("stats", {})
        records = stats.get("records", [])

        today = datetime.now().strftime("%Y-%m-%d")

        today_record = next(
            (x for x in records if x.get("checkin_date") == today),
            {}
        )

        quota_awarded = today_record.get("quota_awarded")

        if quota_awarded is None:
            checkin_body = checkin_data.get("data") or {}
            quota_awarded = checkin_body.get("quota_awarded", 0)

        return {
            "success": True,
            "message": checkin_message or "签到完成",
            "data": {
                "checkin_date": today_record.get("checkin_date", today),
                "quota_awarded": quota_awarded or 0,
                "checked_in_today": stats.get("checked_in_today", False),
                "checkin_count": stats.get("checkin_count", 0),
                "total_checkins": stats.get("total_checkins", 0),
                "total_quota": stats.get("total_quota", 0),
                "records": records
            }
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": f"网络请求失败：{str(e)}",
            "data": {}
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"插件异常：{str(e)}",
            "data": {}
        }