import os
import json
import traceback
import importlib.util
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
from flask import Flask, render_template, request, jsonify
app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.join(BASE_DIR, "plugins")
DATA_DIR = os.path.join(BASE_DIR, "data")
MAX_WORKERS = 5
plugins = {}
# =========================
# 基础工具
# =========================

def ensure_dirs():
    os.makedirs(PLUGIN_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_text():
    return datetime.now().strftime("%Y-%m-%d")


def plugin_data_file(plugin_name):
    return os.path.join(DATA_DIR, f"{plugin_name}.json")


def read_json(path, default_data):
    if not os.path.exists(path):
        return default_data

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default_data


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =========================
# 插件扫描
# =========================

def load_plugins():
    global plugins
    plugins = {}

    os.makedirs(PLUGIN_DIR, exist_ok=True)

    for filename in os.listdir(PLUGIN_DIR):
        if not filename.endswith(".py"):
            continue

        if filename.startswith("__"):
            continue

        file_path = os.path.join(PLUGIN_DIR, filename)
        module_name = filename[:-3]

        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            plugin_name = getattr(module, "PLUGIN_NAME")
            plugin_title = getattr(module, "PLUGIN_TITLE")
            plugin_url = getattr(module, "PLUGIN_URL")
            plugin_desc = getattr(module, "PLUGIN_DESC", "")

            if not hasattr(module, "run"):
                raise Exception("插件缺少 run(username, password) 函数")

            plugins[plugin_name] = {
                "name": plugin_name,
                "title": plugin_title,
                "url": plugin_url,
                "desc": plugin_desc,
                "module": module,
            }

        except Exception as e:
            print(f"[插件加载失败] {filename}: {e}")


# =========================
# 账号数据
# =========================

def default_plugin_data():
    return {
        "accounts": []
    }


def load_plugin_data(plugin_name):
    path = plugin_data_file(plugin_name)
    return read_json(path, default_plugin_data())


def save_plugin_data(plugin_name, data):
    path = plugin_data_file(plugin_name)
    write_json(path, data)


def find_account(data, username):
    for account in data.get("accounts", []):
        if account.get("username") == username:
            return account
    return None


def init_account(username, password):
    return {
        "username": username,
        "password": password,
        "created_at": now_text(),
        "updated_at": now_text(),
        "stats": {
            "last_status": "",
            "last_message": "",
            "last_checkin_time": "",
            "last_checkin_date": "",
            "last_quota_awarded": 0,

            "checked_in_today": False,
            "checkin_count": 0,
            "total_checkins": 0,
            "total_quota": 0,

            "success_times": 0,
            "fail_times": 0,

            "records": []
        }
    }


# =========================
# 插件返回结果标准化
# =========================

def normalize_plugin_result(result):
    """
    插件推荐返回格式：

    {
        "success": True,
        "message": "签到成功",
        "data": {
            "checkin_date": "2026-05-14",
            "quota_awarded": 45485,
            "checked_in_today": True,
            "checkin_count": 1,
            "total_checkins": 1,
            "total_quota": 45485,
            "records": [
                {
                    "checkin_date": "2026-05-14",
                    "quota_awarded": 45485
                }
            ]
        }
    }
    """

    if not isinstance(result, dict):
        return {
            "success": False,
            "message": "插件返回值不是 dict",
            "data": {}
        }

    success = result.get("success", False)

    if success == 1:
        success = True
    elif success == 0:
        success = False

    return {
        "success": bool(success),
        "message": result.get("message", ""),
        "data": result.get("data") or {}
    }


def update_account_stats(account, result):
    stats = account.setdefault("stats", {})
    data = result.get("data") or {}

    success = result.get("success", False)
    message = result.get("message", "")

    checkin_date = data.get("checkin_date") or today_text()
    quota_awarded = int(data.get("quota_awarded") or 0)

    stats["last_status"] = "success" if success else "fail"
    stats["last_message"] = message
    stats["last_checkin_time"] = now_text()

    if success:
        stats["success_times"] = int(stats.get("success_times", 0)) + 1

        stats["last_checkin_date"] = checkin_date
        stats["last_quota_awarded"] = quota_awarded
        stats["checked_in_today"] = data.get(
            "checked_in_today",
            checkin_date == today_text()
        )

        stats["checkin_count"] = int(data.get(
            "checkin_count",
            stats.get("checkin_count", 0)
        ) or 0)

        # 如果插件返回 records，则优先使用接口 records
        if isinstance(data.get("records"), list):
            stats["records"] = data["records"]
        else:
            stats.setdefault("records", [])

            exists = False
            for record in stats["records"]:
                if record.get("checkin_date") == checkin_date:
                    record["quota_awarded"] = quota_awarded
                    exists = True
                    break

            if not exists:
                stats["records"].insert(0, {
                    "checkin_date": checkin_date,
                    "quota_awarded": quota_awarded
                })

        # 优先用接口返回的总统计，没有就本地计算
        stats["total_checkins"] = int(data.get(
            "total_checkins",
            len(stats.get("records", []))
        ) or 0)

        stats["total_quota"] = int(data.get(
            "total_quota",
            sum(int(x.get("quota_awarded") or 0) for x in stats.get("records", []))
        ) or 0)

    else:
        stats["fail_times"] = int(stats.get("fail_times", 0)) + 1

    account["updated_at"] = now_text()


# =========================
# 页面统计
# =========================

def get_overview():
    overview = {
        "site_count": len(plugins),
        "account_count": 0,
        "today_checked_count": 0,
        "total_checkins": 0,
        "total_quota": 0,
        "success_times": 0,
        "fail_times": 0
    }

    for plugin_name in plugins:
        data = load_plugin_data(plugin_name)

        for account in data.get("accounts", []):
            stats = account.get("stats", {})

            overview["account_count"] += 1
            overview["total_checkins"] += int(stats.get("total_checkins") or 0)
            overview["total_quota"] += int(stats.get("total_quota") or 0)
            overview["success_times"] += int(stats.get("success_times") or 0)
            overview["fail_times"] += int(stats.get("fail_times") or 0)

            if stats.get("last_checkin_date") == today_text():
                overview["today_checked_count"] += 1

    return overview


def build_sites_data():
    sites = []

    for plugin_name, plugin in plugins.items():
        data = load_plugin_data(plugin_name)

        sites.append({
            "name": plugin["name"],
            "title": plugin["title"],
            "url": plugin["url"],
            "desc": plugin["desc"],
            "accounts": data.get("accounts", [])
        })

    return sites


# =========================
# 签到执行
# =========================

def run_one_checkin(plugin_name, username):
    if plugin_name not in plugins:
        return {
            "success": False,
            "message": "插件不存在",
            "data": {},
            "username": username,
            "plugin_name": plugin_name
        }

    data = load_plugin_data(plugin_name)
    account = find_account(data, username)

    if not account:
        return {
            "success": False,
            "message": "账号不存在",
            "data": {},
            "username": username,
            "plugin_name": plugin_name
        }

    module = plugins[plugin_name]["module"]

    try:
        raw_result = module.run(
            account.get("username"),
            account.get("password")
        )

        result = normalize_plugin_result(raw_result)

    except Exception as e:
        traceback.print_exc()
        result = {
            "success": False,
            "message": f"插件执行异常：{str(e)}",
            "data": {}
        }

    update_account_stats(account, result)
    save_plugin_data(plugin_name, data)

    return {
        "success": result["success"],
        "message": result["message"],
        "data": result["data"],
        "username": username,
        "plugin_name": plugin_name
    }
def run_batch_checkin(plugin_name, usernames, mode="parallel", interval=None):
    """
    mode: 'parallel' (并发) 或 'sequential' (顺序)
    interval: 顺序模式下的间隔时间(秒)。如果为 None，则在 2-5 秒间随机；如果有值，则固定使用该值。
    """
    results = []
    
    if mode == "sequential":
        # 顺序执行
        for username in usernames:
            res = run_one_checkin(plugin_name, username)
            results.append(res)
            
            # 最后一个不需要等待
            if username != usernames[-1]: 
                # 确定休眠时间
                sleep_time = 0
                
                if interval is not None:
                    # 如果传入了固定时间，直接使用
                    try:
                        sleep_time = float(interval)
                    except:
                        sleep_time = 2 # 异常 fallback
                else:
                    # 如果没有传入时间，随机生成 2-5 秒
                    sleep_time = random.uniform(2, 5)
                
                # 执行休眠
                time.sleep(sleep_time) 
    else:
        # 并发执行 (原有逻辑，不受 interval 影响)
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_map = {}

            for username in usernames:
                future = executor.submit(run_one_checkin, plugin_name, username)
                future_map[future] = username

            for future in as_completed(future_map):
                try:
                    results.append(future.result())
                except Exception as e:
                    results.append({
                        "success": False,
                        "message": str(e),
                        "username": future_map[future],
                        "plugin_name": plugin_name
                    })

    return results
# =========================
# 页面
# =========================

@app.route("/")
def index():
    return render_template(
        "index.html",
        sites=build_sites_data(),
        overview=get_overview(),
        today=today_text()
    )


# =========================
# API
# =========================

@app.route("/api/sites")
def api_sites():
    return jsonify({
        "success": True,
        "sites": build_sites_data(),
        "overview": get_overview()
    })


@app.route("/api/add_account", methods=["POST"])
def api_add_account():
    req = request.get_json() or {}

    plugin_name = req.get("plugin_name")
    username = req.get("username", "").strip()
    password = req.get("password", "").strip()

    if plugin_name not in plugins:
        return jsonify({
            "success": False,
            "message": "插件不存在"
        })

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "用户名和密码不能为空"
        })

    data = load_plugin_data(plugin_name)

    old_account = find_account(data, username)

    if old_account:
        old_account["password"] = password
        old_account["updated_at"] = now_text()
        message = "账号已存在，已更新密码"
    else:
        data.setdefault("accounts", [])
        data["accounts"].append(init_account(username, password))
        message = "账号添加成功"

    save_plugin_data(plugin_name, data)

    return jsonify({
        "success": True,
        "message": message
    })


@app.route("/api/delete_account", methods=["POST"])
def api_delete_account():
    req = request.get_json() or {}

    plugin_name = req.get("plugin_name")
    username = req.get("username")

    if plugin_name not in plugins:
        return jsonify({
            "success": False,
            "message": "插件不存在"
        })

    data = load_plugin_data(plugin_name)

    before_count = len(data.get("accounts", []))

    data["accounts"] = [
        account for account in data.get("accounts", [])
        if account.get("username") != username
    ]

    after_count = len(data.get("accounts", []))

    save_plugin_data(plugin_name, data)

    return jsonify({
        "success": True,
        "message": "账号已删除" if after_count < before_count else "账号不存在"
    })


@app.route("/api/checkin_one", methods=["POST"])
def api_checkin_one():
    req = request.get_json() or {}

    plugin_name = req.get("plugin_name")
    username = req.get("username")

    result = run_one_checkin(plugin_name, username)

    return jsonify(result)
@app.route("/api/checkin_selected", methods=["POST"])
def api_checkin_selected():
    req = request.get_json() or {}

    plugin_name = req.get("plugin_name")
    usernames = req.get("usernames", [])
    mode = req.get("mode", "parallel")
    interval = req.get("interval", None)  # 新增：获取前端传来的间隔

    if plugin_name not in plugins:
        return jsonify({
            "success": False,
            "message": "插件不存在"
        })

    if not usernames:
        return jsonify({
            "success": False,
            "message": "请至少选择一个账号"
        })

    # 传递 interval 给执行函数
    results = run_batch_checkin(plugin_name, usernames, mode=mode, interval=interval)

    return jsonify({
        "success": True,
        "message": f"选中账号签到完成 (模式: {'顺序' if mode == 'sequential' else '并发'})",
        "results": results
    })


@app.route("/api/checkin_all", methods=["POST"])
def api_checkin_all():
    req = request.get_json() or {}

    plugin_name = req.get("plugin_name")
    mode = req.get("mode", "parallel")
    interval = req.get("interval", None) # 新增：获取前端传来的间隔

    if plugin_name not in plugins:
        return jsonify({
            "success": False,
            "message": "插件不存在"
        })

    data = load_plugin_data(plugin_name)

    usernames = [
        account.get("username")
        for account in data.get("accounts", [])
    ]

    if not usernames:
        return jsonify({
            "success": False,
            "message": "该站点暂无账号"
        })

    # 传递 interval 给执行函数
    results = run_batch_checkin(plugin_name, usernames, mode=mode, interval=interval)

    return jsonify({
        "success": True,
        "message": f"该站点全部账号签到完成 (模式: {'顺序' if mode == 'sequential' else '并发'})",
        "results": results
    })
@app.route("/api/reload_plugins", methods=["POST"])
def api_reload_plugins():
    load_plugins()

    return jsonify({
        "success": True,
        "message": "插件已重新扫描",
        "sites": build_sites_data()
    })


# =========================
# 启动
# =========================

if __name__ == "__main__":
    ensure_dirs()
    load_plugins()

    print("已加载插件：")
    for name, plugin in plugins.items():
        print(f"- {plugin['title']} ({name}) {plugin['url']}")

    app.run(host="127.0.0.1", port=5000, debug=True)