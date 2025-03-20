import platform
import sys
import threading
import time
import pyautogui
from pynput import keyboard, mouse

clicking = False
exit_flag = False
duration = 1  # クリックの間隔（秒）
current_keys = set()
click_positions = []  # 記録用リスト
recording = True  # 記録モード

# プラットフォームの識別
platform_name = platform.system()
if platform_name == "Darwin":  # macOS
    toggle_key = {keyboard.Key.ctrl, keyboard.KeyCode(char="z")}  # Ctrl+Z
    quit_key = {keyboard.Key.ctrl, keyboard.KeyCode(char="x")}  # Ctrl+X
elif platform_name == "Windows":  # Windows
    toggle_key = {keyboard.Key.alt_l, keyboard.KeyCode(char="z")}  # Alt+Z
    quit_key = {keyboard.Key.alt_l, keyboard.KeyCode(char="q")}  # Alt+Q
quit_key2 = {keyboard.Key.esc}  # Esc


def click_mouse():
    global exit_flag
    i = 0
    while not exit_flag:
        if clicking and click_positions:
            x, y = click_positions[i % len(click_positions)]
            pyautogui.click(x, y)
            i += 1
        time.sleep(duration)
    print("Click thread exiting...")


def toggle_clicking():
    global clicking
    clicking = not clicking
    print_current_status(True)


def print_current_status(delete_last_line=False):
    global clicking
    if delete_last_line:
        sys.stdout.write("\033[F")  # カーソルを1行上に移動
        sys.stdout.write("\033[K")  # 行を消去
    print("clicking is " + ("\x1b[92mON\x1b[m" if clicking else "\x1b[91mOFF\x1b[m"))


def on_esc():
    global exit_flag
    print("Quit key pressed. Exiting...")
    exit_flag = True


def on_press(key):
    current_keys.add(key)
    if all(k in current_keys for k in toggle_key):
        toggle_clicking()
    elif all(k in current_keys for k in quit_key):
        on_esc()
    elif key in quit_key2:
        on_esc()
    elif key == keyboard.Key.enter:  # Enterキーで記録終了
        global recording
        if not recording:
            print("記録完了! 指定時間ごとに自動クリック開始")
        recording = False


def on_release(key):
    if key in current_keys:
        current_keys.remove(key)


def on_click(x, y, button, pressed):
    if recording and pressed:
        click_positions.append((x, y))
        print(f"記録: {x}, {y}")


# マウスリスナーでクリックを記録
mouse_listener = mouse.Listener(on_click=on_click)
mouse_listener.start()

# キーボードリスナー
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

print("クリックして座標を記録してください (Enterキーで終了)")
while recording:
    time.sleep(0.1)

# 記録終了後、クリックスレッド開始
click_thread = threading.Thread(target=click_mouse)
click_thread.daemon = True
click_thread.start()

if platform_name == "Darwin":
    print(f"{duration}秒ごとに自動でクリックします。")
    print(f"・Ctrl+Z でクリックのオンオフを切り替えます。")
    print(f"・Ctrl+X または Esc で終了します。")
    print()
elif platform_name == "Windows":
    print(f"{duration}秒ごとに自動でクリックします。")
    print(f"・Left Alt+Z でクリックのオンオフを切り替えます。")
    print(f"・Left Alt+Q または Esc で終了します。")
    print()

print_current_status(False)

# メインスレッドで無限ループを実行してホットキーを待機
try:
    while not exit_flag:
        time.sleep(0.1)
finally:
    click_thread.join()
    listener.stop()
    mouse_listener.stop()
    print("プログラムが終了しました")
