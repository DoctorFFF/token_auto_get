import requests
import base64
import json
from nixiang import captcha_encrypt

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh',
    'cache-control': 'no-store',
    'new-api-user': '499356',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://jeniya.top/login',
    'sec-ch-ua': '"Chromium";v="148", "Microsoft Edge";v="148", "Not/A)Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0',
    'x-forwarded-host': 'jeniya.top'
}

# 使用 Session 自动管理 cookie，确保获取验证码和校验接口共享会话
session = requests.Session()
session.headers.update(headers)

# ================= 1. 获取验证码 =================
response = session.get('https://jeniya.top/api/go-captcha-data/click-shape')
captcha_data = response.json()

key = captcha_data['captcha_key']
print(f"🔑 获取到的 key: {key}")
img_base64 = captcha_data['image_base64']
thumb_base64 = captcha_data['thumb_base64']

with open('captcha.png', 'wb') as f:
    f.write(base64.b64decode(img_base64))
with open('thumb.png', 'wb') as f:
    f.write(base64.b64decode(thumb_base64))

print("✅ 已经获取到图片")

# ================= 2. 图像识别获取点击坐标 =================
status_resp = requests.get("http://127.0.0.1:4999/api/status")
print(f"🔍 识别后端状态: {status_resp.json()}")

files = {
    "thumb": open(r"E:\token_auto_get\thumb.png", "rb"),
    "captcha": open(r"E:\token_auto_get\captcha.png", "rb"),
}
recognize_resp = requests.post("http://127.0.0.1:4999/api/click-icon", files=files)
print(f"🔍 识别响应码: {recognize_resp.status_code}")
print(f"🔍 识别结果: {recognize_resp.json()}")
boxes = recognize_resp.json()['boxes']
points = []
for x1, y1, x2, y2 in boxes:
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    points.append([cx, cy])
c = ";".join([f"{p[0]},{p[1]}" for p in points])
print(f"📍 拼接后的坐标字符串: {c}")
# ================= 3. 加密生成 data =================
data = captcha_encrypt(key, c)
print(f"🔐 生成的校验 data: {data}")
# ================= 4. 提交校验（multipart/form-data）=================
check_resp = session.post(
    'https://jeniya.top/api/go-captcha-check-data/click-shape',
    files={
        'key': (None, key),
        'data': (None, data)
    }
)
result = check_resp.json()
print(f"✅ 校验结果: {json.dumps(result, ensure_ascii=False)}")