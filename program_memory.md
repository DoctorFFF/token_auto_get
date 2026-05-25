```markdown
# Program Memory: AutoCheckin System

## 1. 项目概述

本项目是一个极简、插件化的多站点自动签到系统。旨在通过轻量级的架构实现个人账号的自动化管理。

**核心特点：**
*   **真·插件化架构**：每个站点独立为一个 Python 脚本 (`plugins/*.py`)，实现统一接口即可无限扩展，互不干扰。
*   **双模式运行**：
    *   **开发模式**：直接运行 `app.py`，支持热重载，方便调试插件。
    *   **生产模式**：通过 Nuitka 打包为单文件 EXE (`nu_app.exe`)，无需 Python 环境，双击即用。
*   **多账号与批量执行**：支持单账号、选中账号批量、全站点一键签到。提供“并发”与“顺序（含随机间隔）”两种执行策略以应对风控。
*   **零依赖存储**：摒弃数据库，采用 JSON 文件持久化账号信息与签到历史，方便备份与迁移。
*   **可视化前端**：基于 Bootstrap 5 + Chart.js，提供实时日志、统计面板及数据图表。

## 2. 项目架构与文件结构

```text
AutoCheckin/
│
├── app.py                  # [核心] Flask 主程序：API 路由、业务逻辑、插件加载器
├── nu_app.py               # [入口] Nuitka 打包专用入口：处理路径映射、插件包导入
├── requirements.txt        # Python 依赖列表 (Flask, requests, etc.)
├── program_memory.md       # 项目记忆文档
│
├── plugins/                # 📂 插件目录
│   ├── __init__.py         # 插件注册表：定义 BUILTIN_PLUGIN_MODULES
│   ├── daw.py              # 示例插件：DAW Claude
│   └── mhcoding.py         # 示例插件：MHCoding
│
├── data/                   # 📂 数据目录 (自动生成)
│   ├── daw.json            # 站点 'daw' 的账号与签到记录
│   └── mhcoding.json       # 站点 'mhcoding' 的账号与签到记录
│
├── templates/              # 📂 前端模板
│   └── index.html          # 单页应用：UI 展示、JS 交互逻辑
│
└── build/                  # 📂 打包输出目录 (Nuitka 生成)
    └── nu_app.exe          # 最终可执行文件
```

### 数据流示意
```mermaid
graph LR
    User[用户浏览器] -->|HTTP Request| Flask[Flask API (app.py)]
    Flask -->|Load/Save| JSON[(Local JSON Files)]
    Flask -->|Call run()| Plugin[Plugins (plugins/*.py)]
    Plugin -->|HTTP Request| TargetSite[目标网站 API]
```

## 3. 核心模块说明
### 3.1 后端逻辑 (app.py)
- 插件加载：
  开发模式：扫描 `plugins/` 目录下的 `.py` 文件，动态加载模块。
  生产模式：由 `nu_app.py` 覆盖加载逻辑，从 plugins 包中导入预注册模块。
- 签到执行：
  `run_one_checkin`: 执行单个账号签到，更新 JSON 统计数据。
  `run_batch_checkin`: 支持 `parallel` (多线程并发) 和 `sequential` (顺序执行)。
  顺序模式增强：支持固定间隔或随机间隔 (2-5秒)，以模拟人类行为。
- 数据持久化：
  每个插件对应一个 JSON 文件 (`data/{plugin_name}.json`)。
  数据结构包含账号列表，每个账号下嵌套 `stats` (统计信息) 和 `records` (历史记录)。

### 3.2 打包入口 (nu_app.py)
- 路径修正：解决 Nuitka `--onefile` 模式下资源路径 (templates, plugins) 和数据路径 (data) 的分离问题。
  `BUNDLE_DIR`: 资源只读目录 (EXE 内部或临时解压目录)。
  `RUNTIME_DIR`: 数据可写目录 (EXE 所在目录)。
- 插件注册：读取 `plugins/__init__.py` 中的 `BUILTIN_PLUGIN_MODULES` 列表进行导入，避免动态扫描文件在打包后失效的问题。

### 3.3 前端交互 (templates/index.html)
- 状态管理：使用 `pendingCheckinTask` 暂存待执行任务。
- 模态框控制：选择签到模式 (并发/顺序) 及设置间隔时间。
- 实时反馈：通过 `fetch` 调用 API，并在页面日志框实时追加执行结果。
- 图表渲染：使用 Chart.js 渲染签到额度折线图和饼图。

## 4. API 接口文档
基础 URL: `http://127.0.0.1:5000`

| 方法 | 路径 | 描述 | 关键参数 |
| ---- | ---- | ---- | ---- |
| GET | / | 首页渲染 | - |
| GET | /api/sites | 获取所有站点、账号及统计概览 | - |
| POST | /api/add_account | 添加或更新账号 | plugin_name, username, password |
| POST | /api/delete_account | 删除账号 | plugin_name, username |
| POST | /api/checkin_one | 单账号签到 | plugin_name, username |
| POST | /api/checkin_selected | 选中账号批量签到 | plugin_name, usernames[], mode, interval |
| POST | /api/checkin_all | 全站点账号签到 | plugin_name, mode, interval |
| POST | /api/reload_plugins | 重新扫描/加载插件 | - |

**注意：**
- `mode`: `"parallel"` (并发) 或 `"sequential"` (顺序)。
- `interval`: 仅在 sequential 模式下有效。若为 `null` 则随机 2-5s；若为数字则固定间隔。

## 5. 插件开发规范
新建插件文件 `plugins/new_site.py`，必须包含以下要素：

```python
import requests
from datetime import datetime

# 1. 元数据 (必须)
PLUGIN_NAME = "new_site"      # 唯一标识，用于文件名和 API
PLUGIN_TITLE = "New Site"     # 前端显示名称
PLUGIN_URL = "https://example.com"
PLUGIN_DESC = "示例插件描述"

# 2. 核心函数 (必须)
def run(username, password):
    """
    执行签到逻辑
    :return: dict 标准结果格式
    """
    try:
        # --- 业务逻辑开始 ---
        # 1. 登录
        # 2. 签到请求
        # 3. 获取历史/配额
        # --- 业务逻辑结束 ---
        
        return {
            "success": True,
            "message": "签到成功",
            "data": {
                "checkin_date": datetime.now().strftime("%Y-%m-%d"),
                "quota_awarded": 100,       # 今日获得额度
                "checked_in_today": True,
                "checkin_count": 1,         # 本月/连续签到次数
                "total_checkins": 10,       # 累计签到次数
                "total_quota": 1000,        # 累计总额度
                "records": []               # 历史记录列表 (可选，建议返回)
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"异常: {str(e)}",
            "data": {}
        }
```

注册插件： 在 `plugins/__init__.py` 的 `BUILTIN_PLUGIN_MODULES` 列表中添加 `"plugins.new_site"`。

## 6. 部署与打包
### 6.1 开发环境运行
```bash
pip install -r requirements.txt
python app.py
```
访问: `http://127.0.0.1:5000`

### 6.2 Nuitka 打包 (Windows)
前置条件：
- 安装 Nuitka: `pip install nuitka`
- 确保根目录下有 `app.ico` 图标文件 (若无，可移除 `--windows-icon-from-ico` 参数)。
- 确保 `plugins/__init__.py` 已正确注册所有插件。

打包命令：
```bash
python -m nuitka --onefile \
  --standalone \
  --follow-imports \
  --include-package=plugins \
  --include-package=flask \
  --include-package=requests \
  --include-data-dir=templates=templates \
  --output-dir=build \
  --windows-icon-from-ico=app.ico \
  --jobs=12 \
  nu_app.py
```

打包后使用说明：
- 从 `build/` 目录取出 `nu_app.exe`。
- 必须将 `plugins/` 文件夹和 `templates/` 文件夹复制到 `nu_app.exe` 同级目录。

注：虽然 Nuitka 尝试打包这些资源，但在 `nu_app.py` 的逻辑中，我们倾向于让 `templates` 和 `plugins` 作为外部目录存在以便于用户更新插件和模板，而不需重新打包 EXE。如果希望完全单文件，需修改 `nu_app.py` 的路径读取逻辑为从 bundle 内部读取。
当前架构建议：保持 `plugins` 和 `templates` 在外置目录，方便用户自行添加新插件或修改 UI，无需重新编译 EXE。`data/` 目录会自动在 EXE 同级生成。

## 7. 注意事项与安全
- 明文存储风险：账号密码以明文存储在 `data/*.json` 中。严禁将 `data/` 目录上传至 GitHub 或公共网络。已在 `.gitignore` 中忽略该目录。
- 并发风控：并发模式速度快但易触发风控。对于敏感站点，建议使用“顺序模式”并设置较大的随机间隔。
- 插件信任：插件本质是 Python 代码，拥有系统执行权限。请勿运行来源不明的插件。
- Nu_App 路径逻辑：`nu_app.py` 专门处理了打包后的路径问题。如果在开发中修改了资源加载方式，请同步检查 `nu_app.py` 中的 `BUNDLE_DIR` 和 `RUNTIME_DIR` 逻辑。
```