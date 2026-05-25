import os
import sys
import importlib
from pathlib import Path
from threading import Lock

# =========================
# 1. 路径配置 (Nuitka 特有)
# =========================
def get_bundle_dir():
    """
    资源目录：
    - 开发环境：app.py 所在目录
    - Nuitka onefile：解包后的临时目录
    - Nuitka standalone：dist 内程序所在目录
    """
    return Path(__file__).resolve().parent

def get_runtime_dir():
    """
    可写目录：
    - 开发环境：app.py 所在目录
    - 打包后：exe 所在目录
    """
    return Path(sys.argv[0]).resolve().parent

BUNDLE_DIR = get_bundle_dir()
RUNTIME_DIR = get_runtime_dir()
TEMPLATE_DIR = BUNDLE_DIR / "templates"
DATA_DIR = RUNTIME_DIR / "data"

# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)

# =========================
# 2. 导入主应用逻辑
# =========================
# 注意：我们需要先设置好一些全局状态，再导入 app，或者导入后覆盖它们
# 由于 app.py 在模块加载时会执行 ensure_dirs() 和 load_plugins()
# 我们需要在导入 app 之前，或者导入后立即修正路径和插件逻辑

# 这里我们采用“导入后覆盖”的策略，因为 app.py 的 load_plugins 是在 if __name__ == "__main__" 之外定义的
# 但 app.py 底部有 if __name__ == "__main__": load_plugins()
# 所以当我们 import app 时，它不会自动运行 load_plugins，除非我们在 nu_app.py 里手动调用

import app as main_app

# =========================
# 3. 覆盖路径变量 (Monkey Patch)
# =========================
# app.py 中使用的是模块级变量 PLUGIN_DIR 和 DATA_DIR
# 我们需要将它们指向 Nuitka 的正确路径

main_app.PLUGIN_DIR = str(BUNDLE_DIR / "plugins") # 虽然 nu_app 不用这个扫描，但保持一致性好
main_app.DATA_DIR = str(DATA_DIR)

# 重新定义 app.py 中的路径辅助函数，使其使用新的 DATA_DIR
def nu_plugin_data_file(plugin_name):
    return os.path.join(main_app.DATA_DIR, f"{plugin_name}.json")

# 覆盖 app.py 中的 plugin_data_file
main_app.plugin_data_file = nu_plugin_data_file

# =========================
# 4. Nuitka 特有的插件加载逻辑
# =========================

PLUGIN_PACKAGE_NAME = "plugins"
plugin_registry_lock = Lock()
plugin_locks = {}

def get_plugin_lock(plugin_name):
    with plugin_registry_lock:
        if plugin_name not in plugin_locks:
            plugin_locks[plugin_name] = Lock()
        return plugin_locks[plugin_name]

def _get_builtin_plugin_module_names():
    """
    从 plugins/__init__.py 中读取模块列表。
    """
    try:
        package = importlib.import_module(PLUGIN_PACKAGE_NAME)
        module_names = getattr(package, "BUILTIN_PLUGIN_MODULES", None)
        if not isinstance(module_names, list):
            raise RuntimeError(
                "plugins/__init__.py 中必须定义 BUILTIN_PLUGIN_MODULES 列表"
            )
        return module_names
    except Exception as e:
        print(f"[插件初始化失败] {e}")
        return []

def nu_load_plugins():
    """
    替代 app.py 中的 load_plugins，使用包导入方式
    """
    main_app.plugins = {}
    module_names = _get_builtin_plugin_module_names()
    
    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
            plugin_name = getattr(module, "PLUGIN_NAME", None)
            plugin_title = getattr(module, "PLUGIN_TITLE", None)
            plugin_url = getattr(module, "PLUGIN_URL", None)
            plugin_desc = getattr(module, "PLUGIN_DESC", "")
            
            if not plugin_name or not plugin_title or not plugin_url:
                raise Exception("插件缺少 PLUGIN_NAME / PLUGIN_TITLE / PLUGIN_URL")
            if not hasattr(module, "run"):
                raise Exception("插件缺少 run(username, password) 函数")
            
            main_app.plugins[plugin_name] = {
                "name": plugin_name,
                "title": plugin_title,
                "url": plugin_url,
                "desc": plugin_desc,
                "module": module,
                "module_name": module_name,
            }
        except Exception as e:
            print(f"[插件加载失败] {module_name}: {e}")

# 覆盖 app.py 中的 load_plugins
main_app.load_plugins = nu_load_plugins

# =========================
# 5. 增强线程安全 (可选，但推荐)
# =========================
# app.py 中的 run_one_checkin 没有锁。
# 如果 nu_app 需要更高的并发安全性，我们可以包装一下 run_one_checkin
# 但为了保持“向 app.py 靠拢”，我们暂时直接使用 app.py 的逻辑。
# 如果 app.py 的 run_one_checkin 需要加锁，建议在 app.py 里加，或者在这里包装。

# 这里我们选择信任 app.py 的逻辑，因为 app.py 已经更新了 batch_checkin 等逻辑。
# 如果需要针对 nu_app 的特殊锁逻辑，可以在此处包装 main_app.run_one_checkin

# =========================
# 6. 启动
# =========================

if __name__ == "__main__":
    # 1. 确保目录
    main_app.ensure_dirs()
    
    # 2. 加载插件 (使用我们覆盖后的 nu_load_plugins)
    nu_load_plugins()
    
    print("=== Nuitka Mode ===")
    print("资源目录:", BUNDLE_DIR)
    print("运行目录:", RUNTIME_DIR)
    print("数据目录:", DATA_DIR)
    print("已加载插件：")
    for name, plugin in main_app.plugins.items():
        print(f"- {plugin['title']} ({name}) {plugin['url']}")
    # 3. 启动 Flask
    # 注意：使用 main_app.app
    main_app.app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)