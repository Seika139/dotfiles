import json
import sys
import os
import threading
import queue
from pynput import keyboard, mouse

# --- グローバル変数 ---
CONFIG_FILE = "click_map_new.json"
region_points = []
calibrated_region = None
click_map = {}
active_modifiers = set()
click_queue = queue.Queue()
mouse_lock = threading.Lock()


# --- 色付き出力 ---
class Colors:
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"


def print_info(msg):
    print(f"{Colors.OKBLUE}{msg}{Colors.ENDC}")


def print_success(msg):
    print(f"{Colors.OKGREEN}{msg}{Colors.ENDC}")


def print_warning(msg):
    print(f"{Colors.WARNING}{msg}{Colors.ENDC}")


def print_error(msg):
    print(f"{Colors.FAIL}{msg}{Colors.ENDC}")


# --- 修飾キー文字列 ---
def get_modifier_string():
    parts = []
    if any(k in active_modifiers for k in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]):
        parts.append("ctrl")
    if any(
        k in active_modifiers
        for k in [keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr]
    ):
        parts.append("alt")
    if any(k in active_modifiers for k in [keyboard.Key.shift_l, keyboard.Key.shift_r]):
        parts.append("shift")
    if any(k in active_modifiers for k in [keyboard.Key.cmd_l, keyboard.Key.cmd_r]):
        parts.append("cmd")
    return ".".join(parts) + ("+" if parts else "")


# --- 設定ファイル読み込み ---
def load_config():
    global click_map
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
    if not os.path.exists(config_path):
        print_error(f"設定ファイル '{config_path}' が見つかりません。")
        sys.exit(1)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            click_map = json.load(f)
        print_info(f"'{config_path}' から設定を読み込みました。")
    except Exception as e:
        print_error(f"設定ファイルの読み込み失敗: {e}")
        sys.exit(1)


# --- クリックスレッド ---
def click_worker():
    m = mouse.Controller()
    while True:
        try:
            lookup_key, coords = click_queue.get()
            if lookup_key is None:
                break  # 終了信号
            rel_x, rel_y = coords.get("x"), coords.get("y")
            if rel_x is None or rel_y is None:
                continue

            x1, y1, x2, y2 = calibrated_region
            width, height = x2 - x1, y2 - y1
            abs_x, abs_y = x1 + width * rel_x, y1 + height * rel_y

            with mouse_lock:
                original_pos = m.position
                m.position = (abs_x, abs_y)
                m.click(mouse.Button.left, 1)
                m.position = original_pos

            print_success(
                f"キー '{lookup_key}' → ({int(abs_x)}, {int(abs_y)}) をクリック"
            )
        except Exception as e:
            print_error(f"クリック処理エラー: {e}")


# --- キャリブレーション ---
def on_press_calibration(key):
    global region_points, calibrated_region
    if key == keyboard.Key.enter and any(
        k in active_modifiers for k in [keyboard.Key.shift_l, keyboard.Key.shift_r]
    ):
        m = mouse.Controller()
        pos = m.position
        region_points.append(pos)
        print_success(f"座標 {len(region_points)} を記録: {pos}")
        if len(region_points) == 2:
            x1 = min(region_points[0][0], region_points[1][0])
            y1 = min(region_points[0][1], region_points[1][1])
            x2 = max(region_points[0][0], region_points[1][0])
            y2 = max(region_points[0][1], region_points[1][1])
            calibrated_region = (x1, y1, x2, y2)
            print_success(f"キャリブレーション完了: {calibrated_region}")
            return False
    elif key == keyboard.Key.esc:
        print_warning("キャリブレーション中断")
        return False
    elif isinstance(key, keyboard.Key):
        active_modifiers.add(key)


def on_release_calibration(key):
    if key in active_modifiers:
        active_modifiers.remove(key)


# --- メインのキーハンドラー ---
def on_press_main(key):
    if key == keyboard.Key.esc:
        return False

    # 修飾キー管理
    if isinstance(key, keyboard.Key):
        key_name = getattr(key, "name", None)
        if key_name in [
            "ctrl_l",
            "ctrl_r",
            "alt_l",
            "alt_r",
            "alt_gr",
            "shift_l",
            "shift_r",
            "cmd_l",
            "cmd_r",
        ]:
            active_modifiers.add(key)
            return

    # キー名取得（特殊キーも対応）
    key_name = getattr(key, "char", None) or getattr(key, "name", None)
    if not key_name:
        return

    lookup_key = get_modifier_string() + key_name
    if lookup_key in click_map:
        coords = click_map[lookup_key]
        click_queue.put((lookup_key, coords))


def on_release_main(key):
    if key in active_modifiers:
        active_modifiers.remove(key)
    if key == keyboard.Key.esc:
        print_info("プログラム終了")
        click_queue.put((None, None))  # 終了信号
        return False


# --- メイン ---
def main():
    load_config()

    print_info("--- 1. キャリブレーション ---")
    print_info("クリックしたい領域の角にマウスを置き、Shift + Enter を押す")
    with keyboard.Listener(
        on_press=on_press_calibration, on_release=on_release_calibration
    ) as listener:
        listener.join()

    if not calibrated_region:
        print_error("キャリブレーション未完了")
        sys.exit(1)

    active_modifiers.clear()

    print_info("--- 2. クリック待機 ---")
    print_info(f"設定キー: {list(click_map.keys())}")
    print_warning("Esc で終了")

    thread = threading.Thread(target=click_worker, daemon=True)
    thread.start()

    with keyboard.Listener(
        on_press=on_press_main, on_release=on_release_main
    ) as listener:
        listener.join()

    thread.join()
    print_success("プログラム終了")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_info("\n(Ctrl+C) 中断")
        sys.exit(0)
