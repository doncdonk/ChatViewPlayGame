import json, os, sys

def _config_dir():
    """
    exe実行時: exeファイルと同じフォルダ
    スクリプト実行時: game.pyと同じフォルダ
    """
    if getattr(sys, "frozen", False):
        # PyInstallerでexe化された場合はexe本体の場所
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(_config_dir(), "config.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"channel": "", "token": "", "difficulty": "小  9×9   地雷10"}

def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Config] save failed: {e}")
