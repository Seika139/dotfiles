import sys
import threading
import time

import keyboard
import pyautogui

clicking = True
toggle_key = "alt+z"
quit_key = "alt+q"
quit_key2 = "esc"
exit_flag = False
duration = 1  # クリックの間隔（秒）


def click_mouse():
    global exit_flag
    while not exit_flag:
        if clicking:
            pyautogui.click()
        time.sleep(duration)  # クリックの間隔を1秒に設定
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
    print("Esc key pressed. Exiting...")
    exit_flag = True


keyboard.add_hotkey(toggle_key, toggle_clicking)
keyboard.add_hotkey(quit_key, on_esc)
keyboard.add_hotkey(quit_key2, on_esc)

click_thread = threading.Thread(target=click_mouse)
click_thread.daemon = True
click_thread.start()

print(f"{duration}秒ごとに自動でクリックします。")
print(f"・{toggle_key} でクリックのオンオフを切り替えます。")
print(f"・{quit_key} または {quit_key2} で終了します。")
print_current_status(False)

# メインスレッドで無限ループを実行してホットキーを待機
try:
    while not exit_flag:
        time.sleep(0.1)
finally:
    click_thread.join()
    print("プログラムが終了しました")
