Program Memory
1. 项目概述

本项目是一个极简插件化自动签到系统，主要功能是通过插件实现对不同网站/服务的账号自动签到。项目核心特点如下：

插件化：每个站点一个插件（Python 脚本），只需实现统一接口即可扩展。

多账号支持：每个站点可添加多个账号，支持单账号签到、选中账号批量签到、全站点一键签到。

数据持久化：账号和签到记录保存为 JSON 文件，统计数据直接挂在账号下。

前端可视化：使用 Bootstrap + 原生 JS 展示站点信息、账号信息、签到历史和执行日志。

极简易用：无需数据库，纯文件存储，适合本地部署和个人使用。

2. API 设计
2.1 获取站点与统计信息

接口：GET /api/sites
输入：无
输出：

{
  "success": true,
  "sites": [
    {
      "name": "daw",
      "title": "DAW Claude",
      "url": "https://dawclaudecode.com",
      "desc": "DAW Claude 站点自动签到",
      "accounts": [...]
    }
  ],
  "overview": {
    "site_count": 2,
    "account_count": 5,
    "today_checked_count": 3,
    "total_checkins": 20,
    "total_quota": 45000,
    "success_times": 18,
    "fail_times": 2
  }
}
2.2 添加账号

接口：POST /api/add_account
输入：

{
  "plugin_name": "daw",
  "username": "testuser",
  "password": "123456"
}

输出：

{
  "success": true,
  "message": "账号添加成功"
}
2.3 删除账号

接口：POST /api/delete_account
输入：

{
  "plugin_name": "daw",
  "username": "testuser"
}

输出：

{
  "success": true,
  "message": "账号已删除"
}
2.4 单账号签到

接口：POST /api/checkin_one
输入：

{
  "plugin_name": "daw",
  "username": "testuser"
}

输出：

{
  "success": true,
  "message": "签到完成",
  "data": {
    "checkin_date": "2026-05-14",
    "quota_awarded": 1000,
    "checked_in_today": true,
    "checkin_count": 1,
    "total_checkins": 1,
    "total_quota": 1000,
    "records": [...]
  },
  "username": "testuser",
  "plugin_name": "daw"
}
2.5 批量签到（选中账号）

接口：POST /api/checkin_selected
输入：

{
  "plugin_name": "daw",
  "usernames": ["user1", "user2"]
}

输出：

{
  "success": true,
  "message": "选中账号签到完成",
  "results": [ {...}, {...} ]
}
2.6 全站点签到

接口：POST /api/checkin_all
输入：

{
  "plugin_name": "daw"
}

输出：

{
  "success": true,
  "message": "该站点全部账号签到完成",
  "results": [ {...}, {...} ]
}
2.7 插件重新加载

接口：POST /api/reload_plugins
输入：无
输出：

{
  "success": true,
  "message": "插件已重新扫描",
  "sites": [...]
}
3. 工作流

插件扫描

启动系统时扫描 plugins/ 目录

加载每个插件的 PLUGIN_NAME, PLUGIN_TITLE, PLUGIN_URL, PLUGIN_DESC 和 run() 函数

账号管理

添加/删除账号 → 更新对应插件的 JSON 文件

每个账号包含：用户名、密码、创建时间、更新统计数据、签到历史记录

签到执行

单账号：调用插件 run(username, password)

批量或全站点：多线程并发执行 run()

更新 JSON 文件内账号统计

前端显示

首页展示所有站点及账号信息

展示统计信息和签到历史

提供筛选、搜索和执行按钮

执行结果通过 JS 更新日志框

4. 项目架构
checkin_app/
│
├── app.py                  # 主程序，Flask API + 前端渲染
├── requirements.txt        # 依赖
├── README.md               # 项目说明
│
├── plugins/                # 插件目录，每个站点一个插件
│   ├── daw.py
│   └── mhcoding.py
│
├── data/                   # 数据目录，保存 JSON 文件
│   └── daw.json
│
└── templates/
    └── index.html          # 前端页面，Bootstrap + JS

数据流示意：

[前端页面] <---> [Flask API: app.py] <---> [插件: plugins/*.py] <---> [站点接口]
                                           \
                                            --> [本地 JSON: data/*.json]
5. 新 Demo 插件化步骤

如果你自己做了一个新的 demo（比如网站签到功能），想把它变成插件：

创建插件文件

plugins/demo.py

按照插件规范写字段

PLUGIN_NAME = "demo"
PLUGIN_TITLE = "Demo Site"
PLUGIN_URL = "https://demo.com"
PLUGIN_DESC = "Demo 网站自动签到插件"

def run(username, password):
    # 1. 登录 demo 网站
    # 2. 执行签到
    # 3. 获取历史记录
    # 4. 返回标准 dict
    return {
        "success": True,
        "message": "签到完成",
        "data": {
            "checkin_date": "2026-05-14",
            "quota_awarded": 1000,
            "checked_in_today": True,
            "checkin_count": 1,
            "total_checkins": 1,
            "total_quota": 1000,
            "records": []
        }
    }

保存文件 → plugins/demo.py

前端刷新插件

重新启动 Flask 或点击“重新扫描插件”

添加账号

前端添加账号 → JSON 自动生成 data/demo.json

执行签到

前端单账号 / 批量 / 全站点执行

6. 注意事项

JSON 文件存储账号密码，个人使用可以，但公网部署需加密

插件内部 run() 函数负责与站点 API 交互

支持多线程批量执行，提高签到效率

前端日志可以实时查看执行状态