import json
import sys
import os
import threading
import Quartz
from pynput import keyboard

# --- グローバル変数 ---
CONFIG_FILE = "click_map_new.json"
region_points = []
calibrated_region = None
click_map = {}
active_modifiers = set()


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


# --- 修飾キーの状態 ---
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
        print_error(
            f"設定ファイル '{config_path}' が見つかりません。先に click_map_builder.py を実行してください。"
        )
        sys.exit(1)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            click_map = json.load(f)
        print_info(f"'{config_path}' から設定を読み込みました。")
    except Exception as e:
        print_error(f"設定ファイルの読み込みに失敗しました: {e}")
        sys.exit(1)


# --- macOS用クリック関数（カーソルを動かさない） ---
def click_absolute(x, y):
    try:
        point = Quartz.CGPoint(x, y)  # ← tupleではなくCGpointを使う！
        # 左クリック押下
        event_down = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventLeftMouseDown, point, Quartz.kCGMouseButtonLeft
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
        Quartz.CFRelease(event_down)

        # 左クリック解放
        event_up = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventLeftMouseUp, point, Quartz.kCGMouseButtonLeft
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)
        Quartz.CFRelease(event_up)

    except Exception as e:
        print_error(f"クリック失敗: {e}")


# --- キャリブレーション ---
def on_press_calibration(key):
    global region_points, calibrated_region
    if key == keyboard.Key.enter and any(
        k in active_modifiers for k in [keyboard.Key.shift_l, keyboard.Key.shift_r]
    ):
        pos = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
        region_points.append((pos.x, pos.y))
        print_success(
            f"座標 {len(region_points)} を記録しました: ({int(pos.x)}, {int(pos.y)})"
        )
        if len(region_points) == 2:
            x1 = min(region_points[0][0], region_points[1][0])
            y1 = min(region_points[0][1], region_points[1][1])
            x2 = max(region_points[0][0], region_points[1][0])
            y2 = max(region_points[0][1], region_points[1][1])
            calibrated_region = (x1, y1, x2, y2)
            print_success(f"キャリブレーション完了: {calibrated_region}")
            return False
    elif key == keyboard.Key.esc:
        print_warning("キャリブレーションを中断しました。")
        return False
    elif isinstance(key, keyboard.Key):
        active_modifiers.add(key)


def on_release_calibration(key):
    if key in active_modifiers:
        active_modifiers.remove(key)


# --- 実際のクリック実行 ---
def perform_click(lookup_key, coords):
    try:
        rel_x, rel_y = coords.get("x"), coords.get("y")
        if rel_x is None or rel_y is None:
            return

        x1, y1, x2, y2 = calibrated_region
        width, height = x2 - x1, y2 - y1
        abs_x, abs_y = x1 + width * rel_x, y1 + height * rel_y

        click_absolute(abs_x, abs_y)
        print_success(f"キー '{lookup_key}' → ({int(abs_x)}, {int(abs_y)}) をクリック")
    except Exception as e:
        print_error(f"クリック中エラー: {e}")


# --- メインクリックリスナー ---
def on_press_main(key):
    if key == keyboard.Key.esc:
        print_info("プログラムを終了します。")
        return False

    if isinstance(key, keyboard.Key):
        active_modifiers.add(key)
        return

    try:
        key_name = key.char if hasattr(key, "char") else None
        if key_name:
            mod_str = get_modifier_string()
            lookup_key = f"{mod_str}{key_name}"

            if lookup_key in click_map:
                coords = click_map[lookup_key]
                threading.Thread(
                    target=perform_click, args=(lookup_key, coords), daemon=True
                ).start()
    except Exception as e:
        print_error(f"キー処理中にエラー: {e}")


def on_release_main(key):
    if key in active_modifiers:
        active_modifiers.remove(key)


# --- メイン実行 ---
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
        print_error("キャリブレーションが完了しませんでした。終了します。")
        sys.exit(1)

    active_modifiers.clear()
    print_info("\n--- 2. クリック待機モード ---")
    print_info(f"設定されたキー: {list(click_map.keys())}")
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
