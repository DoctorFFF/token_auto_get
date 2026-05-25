#这是一个测试服务器
import time
import json
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# 1. 硬编码账号数据库
# =========================
USERS_DB = {
    "test_user_1": {"password": "123456", "quota": 1000, "last_checkin": None},
    "test_user_2": {"password": "123456", "quota": 2000, "last_checkin": None},
    "test_user_3":  {"password": "123456", "quota": 9999, "last_checkin": None}
}

# 用于模拟服务端的全局状态（重启后重置）
SERVER_START_TIME = time.time()

# =========================
# 2. 辅助函数：详细日志打印
# =========================
def log_request_info(stage, start_time=None):
    """
    打印详细的请求信息，用于风控研究
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    client_ip = request.remote_addr
    method = request.method
    path = request.path
    headers = dict(request.headers)
    
    # 计算耗时
    duration_ms = 0
    if start_time:
        duration_ms = (time.time() - start_time) * 1000

    print("\n" + "="*60)
    print(f"[{timestamp}] 🚀 [{stage}] 收到请求")
    print(f"🌐 来源 IP: {client_ip}")
    print(f"🔗 请求方法: {method} {path}")
    print(f"⏱️  处理耗时: {duration_ms:.2f} ms")
    print("📦 请求头 (Headers):")
    for k, v in headers.items():
        if k.lower() not in ['host', 'content-length']: # 过滤掉一些噪音
            print(f"   {k}: {v}")
    
    if request.is_json:
        print("📝 请求体 (JSON Body):")
        print(f"   {json.dumps(request.get_json(), indent=4)}")
    elif request.data:
        print(f"📝 原始数据: {request.data[:100]}")
        
    print("="*60 + "\n")

# =========================
# 3. API 接口
# =========================

@app.route('/api/user/login', methods=['POST'])
def login():
    start_time = time.time()
    log_request_info("LOGIN", start_time)
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # 模拟网络延迟 (0.5 - 1.5 秒)
    delay = 0.5
    time.sleep(delay)
    
    if username in USERS_DB and USERS_DB[username]['password'] == password:
        print(f"✅ [LOGIN] 用户 {username} 登录成功")
        return jsonify({
            "success": True,
            "message": "登录成功",
            "data": {
                "id": hash(username) % 10000, # 模拟用户ID
                "username": username,
                "token": f"mock_token_{int(time.time())}"
            }
        })
    else:
        print(f"❌ [LOGIN] 用户 {username} 登录失败 (密码错误或用户不存在)")
        return jsonify({
            "success": False,
            "message": "用户名或密码错误"
        }), 401

@app.route('/api/user/checkin', methods=['POST'])
def checkin():
    start_time = time.time()
    
    # 1. 先记录日志，但要注意处理非 JSON 请求的情况
    client_ip = request.remote_addr
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    print("\n" + "="*60)
    print(f"[{timestamp}] 🚀 [CHECKIN] 收到请求")
    print(f"🌐 来源 IP: {client_ip}")
    print(f"🔗 请求方法: POST /api/user/checkin")
    
    # 安全地获取 JSON，防止 400 错误
    try:
        req_json = request.get_json(silent=True) # silent=True 不会因解析失败而报错
        if req_json is None:
            print("📝 请求体: 空或非 JSON")
        else:
            print(f"📝 请求体 (JSON): {json.dumps(req_json)}")
    except Exception as e:
        print(f"⚠️ 解析请求体失败: {e}")

    print("="*60 + "\n")

    # 2. 模拟风控逻辑
    if time.time() % 7 < 1: 
        print("⚠️ [CHECKIN] 触发模拟风控：请求过于频繁或异常")
        return jsonify({
            "success": False,
            "message": "系统繁忙，请稍后再试 (风控拦截)"
        }), 403

    # 3. 随机分配额度
    awarded = int(time.time() * 100) % 5000 + 100
    print(f"💰 [CHECKIN] 签到成功，发放额度: {awarded}")
    
    return jsonify({
        "success": True,
        "message": "签到成功",
        "data": {
            "quota_awarded": awarded,
            "message": f"恭喜获得 {awarded} 积分"
        }
    })
@app.route('/api/user/info', methods=['GET'])
def get_info():
    start_time = time.time()
    log_request_info("GET_INFO", start_time)
    return jsonify({
        "success": True,
        "data": {
            "username": "test_user",
            "total_quota": 100000
        }
    })

if __name__ == '__main__':
    print("🚀 测试服务器启动中...")
    print("📍 监听地址: http://127.0.0.1:5001")
    print("🔑 可用账号:")
    for u, p in USERS_DB.items():
        print(f"   - 用户名: {u}, 密码: {p['password']}")
    app.run(host='127.0.0.1', port=5001, debug=False)