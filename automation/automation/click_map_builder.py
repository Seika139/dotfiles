import json
import sys
import os
from pynput import keyboard, mouse

# --- グローバル変数 ---
OUTPUT_FILE = "click_map_new.json"
region_points = []
calibrated_region = None
new_click_map = {}
current_key_str = None


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
# 修飾キーの状態を保持するセット
active_modifiers = set()


def get_modifier_string():
    """現在の修飾キーの状態から文字列を生成 (例: 'ctrl+shift+')"""
    parts = []
    # Order matters for consistency (e.g., ctrl+shift, not shift+ctrl)
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


# --- 記録モードの処理 ---
def on_click_record(x, y, button, pressed):
    global current_key_str, calibrated_region, new_click_map
    if pressed and button == mouse.Button.left:
        x1, y1, x2, y2 = calibrated_region
        width = x2 - x1
        height = y2 - y1
        if not (x1 <= x <= x2 and y1 <= y <= y2):
            print_warning(
                " クリックされた位置がキャリブレーション領域外です。再度試してください。"
            )
            print_info(
                f"登録したいキー ('{current_key_str}') の位置をクリックしてください..."
            )
            return True
        rel_x = (x - x1) / width
        rel_y = (y - y1) / height
        new_click_map[current_key_str] = {"x": round(rel_x, 4), "y": round(rel_y, 4)}
        print_success(
            f"キー '{current_key_str}' を座標 ({x}, {y}) [相対: ({rel_x:.4f}, {rel_y:.4f})] にマッピングしました。"
        )
        return False


def on_press_record(key):
    global current_key_str
    try:
        if key == keyboard.Key.esc:
            return False

        if isinstance(key, keyboard.Key) and (
            "ctrl" in key.name
            or "alt" in key.name
            or "shift" in key.name
            or "cmd" in key.name
        ):
            active_modifiers.add(key)
            return

        key_name = key.char if hasattr(key, "char") else key.name
        if key_name:
            mod_str = get_modifier_string()
            current_key_str = f"{mod_str}{key_name}"
            print_info(
                f"キー '{current_key_str}' を検出しました。このキーに対応する位置をクリックしてください..."
            )
            with mouse.Listener(on_click=on_click_record) as mouse_listener:
                mouse_listener.join()
            print_info("\n次のキー入力 (修飾キー可) をするか、`Esc`で終了します。")
    except Exception as e:
        print_error(f"[on_press_record] エラー: {e}")


def on_release_record(key):
    if key in active_modifiers:
        active_modifiers.remove(key)


# --- メイン実行部 ---
def main():
    global new_click_map
    print_info("--- マップ作成ツール (修飾キー対応) ---")
    print_info("\n--- 1. キャリブレーション ---")
    print_info("基準となる領域の角にマウスを移動し、`Shift + Enter` を押してください。")
    with keyboard.Listener(
        on_press=on_press_calibration, on_release=on_release_calibration
    ) as listener:
        listener.join()

    if not calibrated_region:
        print_error("キャリブレーションが完了しませんでした。プログラムを終了します。")
        sys.exit(1)

    active_modifiers.clear()  # キャリブレーション時の修飾キーをクリア

    print_info("\n--- 2. 記録モード ---")
    print_info("登録したいキー (例: 'a', 'ctrl+s', 'shift+1') を押してください。")
    print_info("その後、そのキーに割り当てたい場所をマウスでクリックします。")
    print_warning("`Esc` キーで記録を終了し、ファイルに保存します。")

    with keyboard.Listener(
        on_press=on_press_record, on_release=on_release_record
    ) as listener:
        listener.join()

    if new_click_map:
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), OUTPUT_FILE
        )
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(new_click_map, f, indent=2, sort_keys=True)
            print_success(f"\n設定を '{output_path}' に保存しました。")
            print(json.dumps(new_click_map, indent=2, sort_keys=True))
        except IOError as e:
            print_error(f"ファイルの書き込みに失敗しました: {e}")
    else:
        print_warning("\n何も記録されませんでした。ファイルは作成されません。")

    print_success("プログラムが正常に終了しました。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_info("\n(Ctrl+C) プログラムを中断しました。")
        sys.exit(0)
