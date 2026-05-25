import cv2
import numpy as np
import random
import os

out_dir = r"E:\token_auto_get\synthetic"
os.makedirs(out_dir, exist_ok=True)

bg_path = os.path.join(out_dir, "fake_captcha.png")
thumb_path = os.path.join(out_dir, "fake_thumb.png")

W, H = 360, 240
bg = np.ones((H, W, 3), dtype=np.uint8) * 245

# 随机背景噪声
for _ in range(120):
    x = random.randint(0, W - 1)
    y = random.randint(0, H - 1)
    color = random.randint(180, 240)
    cv2.circle(bg, (x, y), random.randint(1, 2), (color, color, color), -1)

icons = []
positions = []

for i in range(6):
    x = random.randint(30, W - 60)
    y = random.randint(30, H - 60)
    size = random.randint(28, 40)
    color = tuple(random.randint(40, 180) for _ in range(3))

    icon_type = random.choice(["circle", "rect", "triangle", "star"])

    if icon_type == "circle":
        cv2.circle(bg, (x, y), size // 2, color, 2)

    elif icon_type == "rect":
        cv2.rectangle(bg, (x-size//2, y-size//2), (x+size//2, y+size//2), color, 2)

    elif icon_type == "triangle":
        pts = np.array([
            [x, y-size//2],
            [x-size//2, y+size//2],
            [x+size//2, y+size//2]
        ])
        cv2.polylines(bg, [pts], True, color, 2)

    elif icon_type == "star":
        cv2.line(bg, (x-size//2, y), (x+size//2, y), color, 2)
        cv2.line(bg, (x, y-size//2), (x, y+size//2), color, 2)
        cv2.line(bg, (x-size//3, y-size//3), (x+size//3, y+size//3), color, 2)
        cv2.line(bg, (x+size//3, y-size//3), (x-size//3, y+size//3), color, 2)

    positions.append((x, y, size, icon_type, color))

cv2.imwrite(bg_path, bg)

# 生成下面的顺序图例，取前 3 个
thumb = np.ones((60, 180, 3), dtype=np.uint8) * 245

for idx, (_, _, size, icon_type, color) in enumerate(positions[:3]):
    x = 30 + idx * 55
    y = 30
    s = 30

    if icon_type == "circle":
        cv2.circle(thumb, (x, y), s // 2, color, 2)
    elif icon_type == "rect":
        cv2.rectangle(thumb, (x-s//2, y-s//2), (x+s//2, y+s//2), color, 2)
    elif icon_type == "triangle":
        pts = np.array([[x, y-s//2], [x-s//2, y+s//2], [x+s//2, y+s//2]])
        cv2.polylines(thumb, [pts], True, color, 2)
    elif icon_type == "star":
        cv2.line(thumb, (x-s//2, y), (x+s//2, y), color, 2)
        cv2.line(thumb, (x, y-s//2), (x, y+s//2), color, 2)
        cv2.line(thumb, (x-s//3, y-s//3), (x+s//3, y+s//3), color, 2)
        cv2.line(thumb, (x+s//3, y-s//3), (x-s//3, y+s//3), color, 2)

cv2.imwrite(thumb_path, thumb)

print("背景图:", bg_path)
print("顺序图:", thumb_path)