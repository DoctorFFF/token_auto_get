# 插件化自动签到系统

这是一个极简版 Flask 插件化自动签到系统。

核心目标：

- 一个 `app.py`
- 一个大模板 `templates/index.html`
- 一个 `plugins` 插件目录
- 一个 `data` 数据目录
- 前端使用 Bootstrap + 原生 JS
- 后端使用 Flask
- 插件自动扫描
- 账号数据和统计数据保存到 JSON 文件

---

## 一、项目结构

```text
checkin_app/
│
├── app.py
├── requirements.txt
├── README.md
│
├── plugins/
│   ├── daw.py
│   └── mhcoding.py
│
├── data/
│   └── 自动生成 JSON 文件
│
└── templates/
    └── index.html
项目打包方法 python -m nuitka --onefile --follow-imports --include-package=plugins --include-data-dir=templates=templates --output-dir=build --windows-icon-from-ico=app.ico --jobs=12 nu_app.py