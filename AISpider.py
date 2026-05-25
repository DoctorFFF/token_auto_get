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
response = requests.get('https://jeniya.top/api/go-captcha-data/click-shape', headers=headers)
captcha_data = response.json()
key=captcha_data['captcha_key']
img_base64 = captcha_data['image_base64']
thumb_base64 = captcha_data['thumb_base64']
with open('captcha.png', 'wb') as f:
    f.write(base64.b64decode(img_base64))
with open('thumb.png', 'wb') as f:
    f.write(base64.b64decode(thumb_base64))
print("已经获取到图片")
#后端配置了图像识别
import requests
url = "http://127.0.0.1:4999/api/click-icon"
resp = requests.get("http://127.0.0.1:4999/api/status")
print(resp.json())#检测后端运行状态
files = {
    "thumb": open(r"E:\token_auto_get\thumb.png", "rb"),
    "captcha": open(r"E:\token_auto_get\captcha.png", "rb"),
}
resp = requests.post(url, files=files)
print(resp.status_code)
print(resp.json())
points=resp.json()['points']
for i in range(len(points)):
    c=f"{points[i][0]},{points[i][1]}"
    c+=";"
c=c[:-2]
