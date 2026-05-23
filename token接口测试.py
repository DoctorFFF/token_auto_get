import requests

# 你提供的 签到 URL（带 token）
url = "https://jeniya.top/api/user/checkin?captcha_token=63606e35-0a2f-4aef-911f-0b03fd8250a3"

# 完整请求头（你抓包的原样）
headers = {
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "zh",
    "cache-control": "no-store",
    "content-length": "0",
    "origin": "https://jeniya.top",
    "pragma": "no-cache",
    "referer": "https://jeniya.top/console",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
    "sec-ch-ua": '"Chromium";v="148", "Microsoft Edge";v="148", "Not/A)Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "new-api-user": "499356",
    "x-forwarded-host": "jeniya.top"
}

# 你抓到的有效 Cookie
cookies = {
    "session": "MTc3OTAyNzQ0OXxEWDhFQVFMX2dBQUJFQUVRQUFEX19QLUFBQWNHYzNSeWFXNW5EQVFBQW1sa0EybHVkQVFGQVAwUFBUZ0djM1J5YVc1bkRBb0FDSFZ6WlhKdVlXMWxCbk4wY21sdVp3d01BQXBFYjJOMGIzSmZSa1pHQm5OMGNtbHVad3dHQUFSeWIyeGxBMmx1ZEFRQ0FBSUdjM1J5YVc1bkRBZ0FCbk4wWVhSMWN3TnBiblFFQWdBQ0JuTjBjbWx1Wnd3SEFBVm5jbTkxY0FaemRISnBibWNNQ1FBSFpHVm1ZWFZzZEFaemRISnBibWNNRWdBUWNHRnpjM2R2Y21SZmRtVnljMmx2YmdOcGJuUUVBZ0FBQm5OMGNtbHVad3dQQUExelpYTnphVzl1WDNSdmEyVnVCbk4wY21sdVp3d2lBQ0EyWlRsa01UaGxZMlZtWldFME5URXdZV1pqTXpBeFpqWTROek5sWWpVMk1RPT18AvBaNZWItM_EyTehq4OYrlIAzznxLIedSrjqLyB5nWU="
}

# ==========================
# 用 Session 发送签到请求
# ==========================
s = requests.Session()
s.headers.update(headers)
s.cookies.update(cookies)

print("正在发送签到请求...")
response = s.post(url, data=b"")  # content-length:0 → 空body

print("\n状态码:", response.status_code)
print("返回结果:", response.text)