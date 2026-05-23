# 🚀 AutoCheckin - 极简插件化自动签到系统

一个轻量级、可扩展的多站点自动签到工具，无需数据库，纯文件存储，一键打包成单文件可执行程序，完美适合个人本地部署使用。

---

## ✨ 项目亮点

- **🔌 真正的插件化架构**：每个站点一个独立Python插件，实现统一接口即可无限扩展
- **👥 多账号全支持**：单账号签到、选中账号批量签到、全站点一键签到
- **📊 完整数据统计**：自动记录签到历史、累计配额、成功率等核心数据
- **🎨 可视化前端**：基于Bootstrap的现代化界面，实时显示执行日志
- **📦 零依赖部署**：Nuitka打包成单EXE，无需安装Python环境，双击即用
- **💾 纯文件存储**：无需MySQL/PostgreSQL，所有数据保存为JSON文件

---

## 🎯 核心功能

| 功能 | 描述 |
|------|------|
| 插件自动扫描 | 启动时自动加载`plugins/`目录下所有符合规范的插件 |
| 账号管理 | 可视化添加/删除账号，数据自动持久化 |
| 多线程签到 | 批量签到采用多线程并发，大幅提升执行效率 |
| 实时日志 | 前端实时显示签到执行过程和结果 |
| 一键重载插件 | 无需重启程序，点击按钮即可扫描新增插件 |
| 数据统计面板 | 总站点数、总账号数、今日已签到、累计签到次数等 |

---

## 🚀 快速开始

### 方式一：直接运行可执行文件（推荐）

1. 下载最新发布的 `nu_app.exe`
2. 将 `plugins/` 和 `templates/` 文件夹放在与 `nu_app.exe` 同一目录下
3. 双击运行 `nu_app.exe`
4. 打开浏览器访问 `http://127.0.0.1:5000` 即可使用

### 方式二：源码运行

1. 克隆仓库
```bash
git clone https://github.com/你的用户名/你的仓库名.git
cd 你的仓库名
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行主程序
```bash
python app.py
```

4. 访问 `http://127.0.0.1:5000`

---

## 📖 使用说明

### 1. 添加账号
- 点击对应站点卡片上的"添加账号"按钮
- 输入用户名和密码，点击确认
- 账号信息会自动保存到 `data/[插件名].json` 文件中

### 2. 执行签到
- **单账号签到**：点击账号右侧的"签到"按钮
- **批量签到**：勾选多个账号，点击"批量签到"按钮
- **全站点签到**：点击站点卡片上的"全部签到"按钮

### 3. 查看历史
- 点击账号右侧的"历史"按钮，查看该账号的所有签到记录
- 包括签到日期、获得配额、执行状态等详细信息

### 4. 管理插件
- 将新插件放入 `plugins/` 目录
- 点击页面顶部的"重新扫描插件"按钮
- 新插件会自动出现在页面中

---

## 🔧 插件开发指南

### 插件规范
创建一个新的签到插件非常简单，只需遵循以下规范：

1. 在 `plugins/` 目录下创建新的Python文件，如 `demo.py`

2. 定义必要的元数据和`run`函数：
```python
# 插件元数据（必须）
PLUGIN_NAME = "demo"          # 插件唯一标识（英文）
PLUGIN_TITLE = "Demo站点"     # 前端显示名称
PLUGIN_URL = "https://demo.com"  # 站点官网
PLUGIN_DESC = "Demo网站自动签到插件"  # 插件描述

def run(username, password):
    """
    签到执行函数（必须实现）
    :param username: 用户名
    :param password: 密码
    :return: 标准格式的结果字典
    """
    try:
        # 在这里实现你的签到逻辑
        # 1. 登录网站
        # 2. 执行签到请求
        # 3. 解析返回结果
        
        return {
            "success": True,
            "message": "签到成功",
            "data": {
                "checkin_date": "2026-05-14",
                "quota_awarded": 1000,  # 本次获得的配额
                "checked_in_today": True,
                "checkin_count": 1,     # 连续签到天数
                "total_checkins": 1,    # 累计签到次数
                "total_quota": 1000,    # 累计获得配额
                "records": []           # 历史记录（可选）
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"签到失败: {str(e)}",
            "data": None
        }
```

3. 保存文件，点击前端"重新扫描插件"即可使用

---

## 🏗️ 项目架构

```
AutoCheckin/
├── nu_app.exe              # Nuitka打包后的单文件可执行程序
├── app.py                  # Flask主程序，API接口+前端渲染
├── requirements.txt        # Python依赖列表
├── README.md               # 项目说明文档
│
├── plugins/                # 插件目录（所有签到插件放在这里）
│   ├── daw.py              # DAW Claude签到插件
│   ├── mhcoding.py         # MH Coding签到插件
│   └── [你的插件].py       # 你自己开发的插件
│
├── data/                   # 数据目录（自动生成）
│   ├── daw.json            # DAW站点的账号和签到数据
│   └── [插件名].json       # 对应插件的数据文件
│
└── templates/              # 前端模板目录
    └── index.html          # 主页面（Bootstrap+原生JS）
```

### 数据流
```
[浏览器前端] <--HTTP--> [Flask API] <--调用--> [签到插件] <--HTTP--> [目标网站]
                                          |
                                          └--读写--> [本地JSON数据文件]
```

---

## 📡 API 文档

### 基础信息
- 基础URL：`http://127.0.0.1:5000`
- 数据格式：JSON
- 请求方法：GET/POST

### 接口列表

#### 1. 获取所有站点和统计信息
```http
GET /api/sites
```
返回所有已加载的插件、账号信息和全局统计数据。

#### 2. 添加账号
```http
POST /api/add_account
Content-Type: application/json

{
  "plugin_name": "daw",
  "username": "your_username",
  "password": "your_password"
}
```

#### 3. 删除账号
```http
POST /api/delete_account
Content-Type: application/json

{
  "plugin_name": "daw",
  "username": "your_username"
}
```

#### 4. 单账号签到
```http
POST /api/checkin_one
Content-Type: application/json

{
  "plugin_name": "daw",
  "username": "your_username"
}
```

#### 5. 批量签到
```http
POST /api/checkin_selected
Content-Type: application/json

{
  "plugin_name": "daw",
  "usernames": ["user1", "user2", "user3"]
}
```

#### 6. 全站点签到
```http
POST /api/checkin_all
Content-Type: application/json

{
  "plugin_name": "daw"
}
```

#### 7. 重新加载插件
```http
POST /api/reload_plugins
```
重新扫描`plugins/`目录，加载新增或修改的插件。

---

## 📦 打包说明

使用Nuitka将项目打包成单文件可执行程序：

```bash
python -m nuitka --onefile --follow-imports --include-package=plugins \
  --include-data-dir=templates=templates --output-dir=build \
  --windows-icon-from-ico=app.ico --jobs=12 nu_app.py
```

打包完成后，可执行文件会生成在 `build/` 目录下。

**打包参数说明**：
- `--onefile`：打包成单个EXE文件
- `--follow-imports`：自动跟踪并包含所有依赖
- `--include-package=plugins`：包含整个plugins包
- `--include-data-dir=templates=templates`：包含templates目录
- `--jobs=12`：使用12个CPU核心并行编译，加速打包过程

---

## ⚠️ 注意事项

1. **安全提示**：账号密码以明文形式存储在JSON文件中，**仅限个人本地使用**，切勿部署到公网或分享给他人
2. **插件安全**：只运行你信任的插件，恶意插件可能会窃取你的账号信息
3. **使用限制**：请遵守目标网站的使用条款，不要过于频繁地执行签到操作
4. **数据备份**：定期备份`data/`目录下的JSON文件，防止数据丢失
5. **网络环境**：部分网站可能需要特定的网络环境才能正常访问

---

## 📄 许可证

本项目采用 MIT 许可证，详情请参见 [LICENSE](LICENSE) 文件。

---

## ⭐ 支持本项目

如果你觉得这个项目对你有帮助，欢迎给个Star⭐支持一下！

有问题或建议可以提交Issue，也欢迎提交PR贡献新的插件或功能。