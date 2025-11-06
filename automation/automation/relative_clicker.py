import json
import sys
import os
from pynput import keyboard, mouse
import threading

# --- グローバル変数 ---
CONFIG_FILE = "click_map_new.json"
region_points = []
calibrated_region = None
click_map = {}
mouse_lock = threading.Lock()  # 🧩 マウス操作の排他制御用


# --- 色付け用 (ターミナル出力) ---
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_info(message):
    print(f"{Colors.OKBLUE}{message}{Colors.ENDC}")


def print_success(message):
    print(f"{Colors.OKGREEN}{message}{Colors.ENDC}")


def print_warning(message):
    print(f"{Colors.WARNING}{message}{Colors.ENDC}")


def print_error(message):
    print(f"{Colors.FAIL}{message}{Colors.ENDC}")


# --- 共通: 修飾キーの状態管理 ---
active_modifiers = set()


def get_modifier_string():
    """現在の修飾キーの状態から文字列を生成 (例: 'ctrl+shift+')"""
    parts = []
    # 順序を固定して一貫性を保つ
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


# --- 設定ファイルの読み込み ---
def load_config():
    global click_map
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
    if not os.path.exists(config_path):
        print_error(
            f"設定ファイル '{config_path}' が見つかりません。先に click_map_builder.py を実行してください。"
        )
        sys.exit(1)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            click_map = json.load(f)
        print_info(f"'{config_path}' から設定を読み込みました。")
    except (json.JSONDecodeError, IOError) as e:
        print_error(f"設定ファイルの読み込みに失敗しました: {e}")
        sys.exit(1)


# --- キャリブレーション処理 ---
def on_press_calibration(key):
    global region_points, calibrated_region
    if key == keyboard.Key.enter and any(
        k in active_modifiers for k in [keyboard.Key.shift_l, keyboard.Key.shift_r]
    ):
        m = mouse.Controller()
        pos = m.position
        region_points.append(pos)
        print_success(f"座標 {len(region_points)} を記録しました: {pos}")
        if len(region_points) == 2:
            x1 = min(region_points[0][0], region_points[1][0])
            y1 = min(region_points[0][1], region_points[1][1])
            x2 = max(region_points[0][0], region_points[1][0])
            y2 = max(region_points[0][1], region_points[1][1])
            calibrated_region = (x1, y1, x2, y2)
            print_success(f"キャリブレーション完了。領域: {calibrated_region}")
            return False
    elif key == keyboard.Key.esc:
        print_warning("キャリブレーションを中断しました。")
        return False
    elif isinstance(key, keyboard.Key) and (
        "ctrl" in key.name
        or "alt" in key.name
        or "shift" in key.name
        or "cmd" in key.name
    ):
        active_modifiers.add(key)


def on_release_calibration(key):
    if key in active_modifiers:
        active_modifiers.remove(key)


# --- メインのクリック処理 ---
def perform_click(lookup_key, coords):
    try:
        rel_x, rel_y = coords.get("x"), coords.get("y")
        if rel_x is None or rel_y is None:
            return

        x1, y1, x2, y2 = calibrated_region
        width, height = x2 - x1, y2 - y1
        abs_x, abs_y = x1 + width * rel_x, y1 + height * rel_y

        # 🧩 ロックをかけて「同時にマウスを動かさない」
        with mouse_lock:
            m = mouse.Controller()
            original_pos = m.position
            m.position = (abs_x, abs_y)
            m.click(mouse.Button.left, 1)
            m.position = original_pos

        print(f"キー '{lookup_key}' をクリック: ({int(abs_x)}, {int(abs_y)})")

    except Exception as e:
        print_error(f"クリック処理中にエラー: {e}")


# --- メインのクリック処理 ---
def on_press_main(key):
    global calibrated_region, click_map
    if key == keyboard.Key.esc:
        return False

    # 修飾キーの管理を明確化
    if isinstance(key, keyboard.Key):
        key_name = key.name or ""
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

    try:
        key_name = getattr(key, "char", None) or getattr(key, "name", None)
        if not key_name:
            return

        mod_str = get_modifier_string()
        lookup_key = f"{mod_str}{key_name}"

        if lookup_key in click_map:
            coords = click_map[lookup_key]
            # スレッドでクリック処理を非同期化
            threading.Thread(
                target=perform_click, args=(lookup_key, coords), daemon=True
            ).start()

    except Exception as e:
        print_error(f"エラーが発生しました: {e}")


def on_release_main(key):
    if key in active_modifiers:
        active_modifiers.remove(key)
    if key == keyboard.Key.esc:
        print_info("プログラムを終了します。")
        return False


# --- メイン実行部 ---
def main():
    load_config()
    print_info("\n--- 1. キャリブレーション ---")
    print_info(
        "クリックしたい領域の角にマウスを移動し、`Shift + Enter` を押してください。"
    )
    with keyboard.Listener(
        on_press=on_press_calibration, on_release=on_release_calibration
    ) as listener:
        listener.join()

    if not calibrated_region:
        print_error("キャリブレーションが完了しませんでした。プログラムを終了します。")
        sys.exit(1)

    active_modifiers.clear()

    print_info("\n--- 2. クリック待機モード ---")
    print_info(f"設定されたキー ({list(click_map.keys())}) を押すとクリックします。")
    print_warning("`Esc` キーで終了します。")

    with keyboard.Listener(
        on_press=on_press_main, on_release=on_release_main
    ) as listener:
        listener.join()

    print_success("\nプログラムが正常に終了しました。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_info("\n(Ctrl+C) プログラムを中断しました。")
        sys.exit(0)
