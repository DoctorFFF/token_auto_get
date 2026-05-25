import os
import base64
import random
from pathlib import Path
import torch
import AntiCAP
from flask import Flask, request, jsonify

app = Flask(__name__)

Atc = AntiCAP.Handler(show_banner=True)


def file_to_base64(file_storage):
    return base64.b64encode(file_storage.read()).decode("utf-8")


def box_to_random_point(box, margin_ratio=0.2):
    x1, y1, x2, y2 = box

    w = x2 - x1
    h = y2 - y1

    mx = int(w * margin_ratio)
    my = int(h * margin_ratio)

    safe_x1 = x1 + mx
    safe_x2 = x2 - mx
    safe_y1 = y1 + my
    safe_y2 = y2 - my

    if safe_x1 >= safe_x2:
        safe_x1, safe_x2 = x1, x2

    if safe_y1 >= safe_y2:
        safe_y1, safe_y2 = y1, y2

    return [
        random.randint(safe_x1, safe_x2),
        random.randint(safe_y1, safe_y2)
    ]


@app.route("/api/status", methods=["GET"])
def status():
    gpu_ready = torch.cuda.is_available()

    return jsonify({
        "ok": True,
        "torch_version": torch.__version__,
        "cuda_available": gpu_ready,
        "gpu_name": torch.cuda.get_device_name(0) if gpu_ready else None,
        "device": "cuda" if gpu_ready else "cpu"
    })


@app.route("/api/click-icon", methods=["POST"])
def click_icon():
    try:
        if "thumb" not in request.files:
            return jsonify({"ok": False, "error": "缺少提示图字段 thumb"}), 400

        if "captcha" not in request.files:
            return jsonify({"ok": False, "error": "缺少背景图字段 captcha"}), 400

        thumb_base64 = file_to_base64(request.files["thumb"])
        captcha_base64 = file_to_base64(request.files["captcha"])

        boxes = Atc.ClickIcon_Order(
            order_img_base64=thumb_base64,
            target_img_base64=captcha_base64
        )

        points = [box_to_random_point(box) for box in boxes]

        return jsonify({
            "ok": True,
            "points": points,
            "count": len(points),
            "device": "cuda" if torch.cuda.is_available() else "cpu"
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=4999,
        debug=False
    )