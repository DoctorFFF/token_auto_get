import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import base64
import glob
from ultralytics import YOLO

# 尝试导入 AntiCAP，如果未安装请 pip install AntiCAP (或根据实际安装方式)
try:
    import AntiCAP
except ImportError:
    raise ImportError("请安装 AntiCAP 库: pip install AntiCAP")

# ================= 配置路径 =================
# 输入图片
THUMB_SRC = r"E:\token_auto_get\thumb.png"       # 指示图（需要被切割）
CAPTCHA_SRC = r"E:\token_auto_get\captcha.png"    # 背景大图（需要被检测）

# 输出目录
THUMB_CROPS_DIR = r"E:\token_auto_get\thumb_crops" # 存放切割后的指示图小块
DEBUG_OUT_DIR = r"E:\token_auto_get\debug_crops"   # 存放检测裁剪图和最终结果图

# YOLO 模型路径
MODEL_PATH = r"D:\conda\envs\anticap\lib\site-packages\AntiCAP\AntiCAP-Models\[AntiCAP]-Detection_Icon-YOLO.pt"
# Siamese 相似度模型路径
SIM_MODEL_PATH = r"D:\conda\envs\anticap\lib\site-packages\AntiCAP\AntiCAP-Models\[AntiCAP]-Siamese-ResNet18.onnx"

# 切割参数 (来自 查看图像.py)
CUT_X1 = 42
CUT_X2 = 81

# YOLO 检测阈值
YOLO_CONF_THRESHOLD = 0.1
YOLO_IOU_THRESHOLD = 0.5

# ================= 辅助函数 =================

def img_to_base64(path):
    """将图片文件转换为 base64 字符串"""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def crop_thumb_image(src_path, output_dir):
    """
    根据 查看图像.py 的逻辑切割指示图
    返回切割后的图片路径列表
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[Info] 创建目录: {output_dir}")

    try:
        img = mpimg.imread(src_path)
        height, width = img.shape[:2]
        print(f"[Info] 指示图原始尺寸: 宽={width}, 高={height}")

        crops_info = [
            {"name": "thumb1.png", "x_start": 0,      "x_end": CUT_X1},
            {"name": "thumb2.png", "x_start": CUT_X1, "x_end": CUT_X2},
            {"name": "thumb3.png", "x_start": CUT_X2, "x_end": width}
        ]

        saved_paths = []
        for crop_info in crops_info:
            x_start = crop_info["x_start"]
            x_end = crop_info["x_end"]
            filename = crop_info["name"]
            
            if x_start >= x_end or x_start >= width:
                print(f"[Warn] 跳过 {filename}: 切割范围无效")
                continue
            
            # 切割: [行, 列] -> [y, x]
            cropped_img = img[:, x_start:x_end]
            save_path = os.path.join(output_dir, filename)
            
            # 保存处理
            if cropped_img.dtype == np.float32 or cropped_img.dtype == np.float64:
                plt.imsave(save_path, cropped_img)
            else:
                plt.imsave(save_path, cropped_img.astype(np.uint8))
            
            saved_paths.append(save_path)
            print(f"[Success] 已保存指示图切片: {save_path}")
        
        return saved_paths

    except Exception as e:
        print(f"[Error] 切割指示图失败: {e}")
        return []

def detect_and_crop_captcha(src_path, model_path, output_dir, conf_thresh=0.1, iou_thresh=0.5):
    """
    使用 YOLO 检测背景图中的图标，并裁剪保存
    返回检测框信息列表和对应的裁剪图路径列表
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 加载 YOLO 模型
    print("[Info] 加载 YOLO 模型...")
    model = YOLO(model_path)
    
    # 执行检测
    print(f"[Info] 正在检测背景图: {src_path} (conf={conf_thresh})")
    results = model(src_path, conf=conf_thresh, iou=iou_thresh)
    
    img = cv2.imread(src_path)
    if img is None:
        raise RuntimeError(f"无法读取背景图: {src_path}")
    
    h, w = img.shape[:2]
    detected_boxes = []
    crop_paths = []

    box_index = 0
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            
            # 边界检查
            x1 = max(0, min(x1, w - 1))
            x2 = max(0, min(x2, w))
            y1 = max(0, min(y1, h - 1))
            y2 = max(0, min(y2, h))
            
            # 裁剪
            crop = img[y1:y2, x1:x2]
            if crop.size == 0:
                continue
                
            crop_filename = f"detected_icon_{box_index}.png"
            crop_path = os.path.join(output_dir, crop_filename)
            cv2.imwrite(crop_path, crop)
            
            detected_boxes.append({
                "index": box_index,
                "coords": (x1, y1, x2, y2),
                "conf": conf,
                "crop_path": crop_path # 保存路径以便后续比对
            })
            crop_paths.append(crop_path)
            
            box_index += 1

    print(f"[Success] 检测到 {len(detected_boxes)} 个候选框，已裁剪保存至 {output_dir}")
    return detected_boxes, crop_paths

def find_best_matches_for_each_thumb(thumb_paths, detected_boxes, sim_model_path):
    """
    针对每一个 Thumb，在所有的 detected_boxes 中找到相似度最高的那个。
    返回一个列表，每个元素对应一个 thumb 的最佳匹配结果。
    """
    Atc = AntiCAP.Handler(show_banner=False)
    
    # 预加载所有检测框的 base64，避免重复读取文件
    detected_b64_list = []
    for box_info in detected_boxes:
        try:
            b64 = img_to_base64(box_info["crop_path"])
            detected_b64_list.append(b64)
        except Exception as e:
            print(f"[Warn] 读取检测框图片失败: {e}")
            detected_b64_list.append(None)

    results_map = [] # 存储每个 thumb 的最佳匹配信息

    print(f"[Info] 开始逐个 Thumb 比对...")

    for t_idx, t_path in enumerate(thumb_paths):
        t_name = os.path.basename(t_path)
        t_b64 = img_to_base64(t_path)
        
        best_match_for_this_thumb = {
            "thumb_name": t_name,
            "max_sim": -1.0,
            "matched_box_info": None # 包含 coords, index 等
        }
        
        for d_idx, box_info in enumerate(detected_boxes):
            d_b64 = detected_b64_list[d_idx]
            if d_b64 is None:
                continue
                
            try:
                sim_score = Atc.Compare_Image_Similarity(
                    image1_base64=t_b64,
                    image2_base64=d_b64,
                    sim_onnx_model_path=sim_model_path
                )
                
                # 处理返回值格式
                if isinstance(sim_score, dict):
                    sim_val = sim_score.get('similarity', 0)
                else:
                    sim_val = float(sim_score)
                
                if sim_val > best_match_for_this_thumb["max_sim"]:
                    best_match_for_this_thumb["max_sim"] = sim_val
                    best_match_for_this_thumb["matched_box_info"] = box_info
                    
            except Exception as e:
                print(f"[Warn] 比对失败 ({t_name} vs Box {d_idx}): {e}")

        results_map.append(best_match_for_this_thumb)
        print(f"  [{t_name}] 最佳相似度: {best_match_for_this_thumb['max_sim']:.4f}, "
              f"匹配框索引: {best_match_for_this_thumb['matched_box_info']['index'] if best_match_for_this_thumb['matched_box_info'] else 'None'}")

    return results_map

def visualize_debug(captcha_src_path, detected_boxes, results_map, output_dir):
    """
    生成调试可视化图 (final_result_visualization.png)
    画出所有检测框，并将全局最高相似度的框标绿（可选，这里主要展示所有框）
    """
    img = cv2.imread(captcha_src_path)
    if img is None:
        return

    # 找出全局最高相似度的框索引，用于高亮
    global_best_idx = -1
    global_max_sim = -1.0
    
    for res in results_map:
        if res["matched_box_info"]:
            if res["max_sim"] > global_max_sim:
                global_max_sim = res["max_sim"]
                global_best_idx = res["matched_box_info"]["index"]

    for box_info in detected_boxes:
        x1, y1, x2, y2 = box_info["coords"]
        
        if box_info["index"] == global_best_idx:
            color = (0, 255, 0) # 绿色：全局最佳
            thickness = 3
            label = f"Best({global_max_sim:.2f})"
        else:
            color = (0, 0, 255) # 红色：其他
            thickness = 1
            label = f"ID:{box_info['index']}"
            
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        # 调试图中保留简单标签，不显示路径
        cv2.putText(img, label, (x1, max(20, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    save_path = os.path.join(output_dir, "final_result_visualization.png")
    cv2.imwrite(save_path, img)
    print(f"[Success] 调试可视化结果已保存: {save_path}")

def visualize_result_display(captcha_src_path, results_map, output_dir):
    """
    生成结果展示图 (result_display.png)
    按照 thumb1, thumb2, thumb3 的顺序，画出它们在背景图中对应的最佳匹配框，并打上标签 thumb 1, thumb 2...
    """
    img = cv2.imread(captcha_src_path)
    if img is None:
        return

    # 定义颜色池，方便区分不同的 thumb
    colors = [
        (255, 0, 0),   # Blue (OpenCV is BGR) -> Thumb 1
        (0, 255, 0),   # Green -> Thumb 2
        (0, 0, 255),   # Red -> Thumb 3
        (255, 255, 0), # Cyan
        (255, 0, 255), # Magenta
        (0, 255, 255)  # Yellow
    ]

    used_boxes_indices = set() # 记录已经画过的框，避免重复绘制导致覆盖（虽然通常不同thumb匹配不同框）

    for t_idx, res in enumerate(results_map):
        thumb_label = f"thumb {t_idx + 1}"
        color = colors[t_idx % len(colors)]
        
        if res["matched_box_info"] and res["max_sim"] > 0.5: # 设定一个最低相似度阈值，比如 0.5，避免强行匹配
            box_info = res["matched_box_info"]
            x1, y1, x2, y2 = box_info["coords"]
            
            # 画框
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
            
            # 准备标签文本
            label_text = f"{thumb_label} ({res['max_sim']:.2f})"
            
            # 计算标签位置，确保在图片内
            font_scale = 0.8
            thickness = 2
            (text_w, text_h), baseline = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
            
            label_y = max(text_h + 10, y1 - 10)
            label_x = x1
            
            # 画标签背景
            cv2.rectangle(img, (label_x, label_y - text_h - baseline), (label_x + text_w, label_y + baseline), color, -1)
            # 画标签文字 (白色)
            cv2.putText(img, label_text, (label_x, label_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)
            
            used_boxes_indices.add(box_info["index"])
        else:
            print(f"[Warn] {thumb_label} 未找到有效匹配或相似度太低 ({res['max_sim']:.4f})")

    save_path = os.path.join(output_dir, "result_display.png")
    cv2.imwrite(save_path, img)
    print(f"[Success] 结果展示图已保存: {save_path}")


# ================= 主流程 =================

def main():
    print("="*30)
    print("开始执行自动化识别流程")
    print("="*30)

    # 1. 切割指示图 (Thumb)
    print("\n[Step 1] 切割指示图...")
    thumb_paths = crop_thumb_image(THUMB_SRC, THUMB_CROPS_DIR)
    if not thumb_paths:
        print("[Error] 指示图切割失败，退出。")
        return

    # 2. 检测并裁剪背景图 (Captcha)
    print("\n[Step 2] 检测并裁剪背景图...")
    detected_boxes, crop_paths = detect_and_crop_captcha(
        CAPTCHA_SRC, 
        MODEL_PATH, 
        DEBUG_OUT_DIR, 
        YOLO_CONF_THRESHOLD, 
        YOLO_IOU_THRESHOLD
    )
    if not crop_paths:
        print("[Error] 背景图中未检测到任何图标，退出。")
        return

    # 3. 相似度比对 (针对每个 Thumb 找最佳匹配)
    print("\n[Step 3] 执行相似度比对 (每个 Thumb 独立匹配)...")
    results_map = find_best_matches_for_each_thumb(thumb_paths, detected_boxes, SIM_MODEL_PATH)

    # 4. 输出文本结果
    print("\n" + "="*30)
    print("详细匹配结果:")
    for res in results_map:
        box_idx = res["matched_box_info"]["index"] if res["matched_box_info"] else "N/A"
        print(f"{res['thumb_name']} -> 最佳匹配框 ID: {box_idx}, 相似度: {res['max_sim']:.4f}")
    print("="*30)

    # 5. 生成可视化图片
    print("\n[Step 4] 生成可视化图片...")
    
    # A. 调试图：显示所有检测框和全局最佳
    visualize_debug(CAPTCHA_SRC, detected_boxes, results_map, DEBUG_OUT_DIR)
    
    # B. 结果展示图：按 Thumb 顺序标注
    visualize_result_display(CAPTCHA_SRC, results_map, DEBUG_OUT_DIR)
    
    print("\n流程结束。")

if __name__ == "__main__":
    main()