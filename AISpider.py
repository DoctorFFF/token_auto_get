import requests
import base64
import json
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
img_base64 = captcha_data['image_base64']
thumb_base64 = captcha_data['thumb_base64']
with open('captcha.png', 'wb') as f:
    f.write(base64.b64decode(img_base64))
with open('thumb.png', 'wb') as f:
    f.write(base64.b64decode(thumb_base64))
print("已经获取到图片")
# ===== 下面是新增部分：与本地 Ollama 通信的通用模板 =====
import requests
import json
import base64

# Ollama接口地址
OLLAMA_API = "http://127.0.0.1:11434/api/chat"
# 优先轻量验证码专用模型
MODEL = "qwen2.5vl:7b"
def img_to_base64(img_path: str) -> str:
    """图片转base64"""
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
def get_captcha_click_pos(main_img_path: str, tip_img_path: str):
    main_b64 = img_to_base64(main_img_path)
    tip_b64 = img_to_base64(tip_img_path)
    prompt = """
任务：根据提示图中的图形顺序，在主图中找出对应图形的点击坐标。

输入说明：
- 第1张图片：主图，是需要点击的背景图。
- 第2张图片：提示图，只用于告诉你需要点击的图形顺序。
- 不要识别按钮、文字、边框、水印等无关元素。

识别规则：
1. 读取第2张图片中的图形顺序。
2. 在第1张主图中，按顺序找到对应图形。
3. 忽略颜色、纹理、明暗、大小差异，只按外轮廓形状匹配。
4. 若主图中目标带有数字标记、局部遮挡或覆盖，忽略这些覆盖物，仍按原始图形轮廓判断。
5. 返回每个目标在主图中的大致中心坐标。
6. 坐标原点定义为主图左下角：
   - x 从左向右递增
   - y 从下向上递增
7. 坐标必须基于主图本身，不允许基于页面截图或外层容器。
8. 返回的是主图内部坐标，不是整张页面坐标
9. 若输出归一化坐标，必须基于主图宽高归一化
输出要求：
- 仅返回纯 JSON 数组
- 禁止输出任何解释、说明、注释、markdown
- 输出格式：根据第2张图片中的图形数量决定是
[{"x":数值,"y":数值},{"x":数值,"y":数值}]或者[{"x":数值,"y":数值},{"x":数值,"y":数值},{"x":数值,"y":数值}]
输出结果数量要对的上"""
    payload = {
        "model": MODEL,
        "stream": False,
        "options": {
            "temperature": 0.1
        },
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [main_b64, tip_b64]
            }
        ]
    }
    try:
        res = requests.post(OLLAMA_API, json=payload, timeout=150)
        res.raise_for_status()
        reply = res.json()["message"]["content"]
        return reply
    except Exception as e:
        return f"请求异常：{str(e)}"
if __name__ == "__main__":
    res_data = get_captcha_click_pos("captcha.png", "thumb.png")
    print(res_data)