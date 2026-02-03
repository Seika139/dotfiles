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
            pyautogui.click()  # 二重の極み
        time.sleep(duration)  # クリックの間隔を1秒に設定
    print("Click thread exiting...")


def toggle_clicking():
    global clicking
    clicking = not clicking
    print_current_status(True)


def print_current_status(delete_last_line: bool = False):
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


"""
# MJ

七対子 2翻25符

| 翻 | 1 | 2 | 3 | 4 |
| 子 | - | (1600ロンのみ) | 800/1600(3200) | 1600/3200(6400) |
| 親 | - | (2400ロンのみ) | 1600オール(4800) | 3200オール(9600) |

翻数 子 親
5 2000/4000(8000) 4000オール(12000)
6,7 3000/6000(12000) 6000オール(18000)
8,9,10 4000/8000(16000) 8000オール(24000)
11,12 6000/12000(24000) 12000オール(36000)
13以上 8000/16000(32000) 16000オール(48000)


平和 20符

それ以外

基本符
20

上がり
面前ロン 10
ツモ 2

待ち
両面・シャボ以外 2

雀頭
役牌 2

面子 中張牌  19字牌
明刻  2 4
暗刻  4 8
明槓  8 16
暗槓  16 32


子

|符\翻|              1 |               2 |                 3 |                 4 |
|  20 |                |         400/700 |          700/1300 |         1300/2600 | # 平和ツモのみ
|  30 |  300/500(1000) |  500/1000(2000) |   1000/2000(4000) | 2000/3900(7700)*1 | # *1 ルールによっては満貫
|  40 |  400/700(1300) |  700/1300(2600) |   1300/2600(5200) |              満貫 |
|  50 |  400/800(1600) |  800/1600(3200) |   1600/3200(6400) |              満貫 |
|  60 | 500/1000(2000) | 1000/2000(3900) | 2000/3900(7700)*1 |              満貫 | # *1 ルールによっては満貫
|  70 | 600/1200(2300) | 1200/2300(4500) |              満貫 |              満貫 |
|  80 | 700/1300(2600) | 1300/2600(5200) |              満貫 |              満貫 |
|  90 | 800/1500(2900) | 1500/2900(5800) |              満貫 |              満貫 |
| 100 | 800/1600(3200) | 1600/3200(6400) |              満貫 |              満貫 |
| 110 | 900/1800(3600) | 1800/3600(7100) |              満貫 |              満貫 |


親

|符\翻|                1 |                 2 |                  3  |                   4 |
|  20 |                  |         700オール |         1300オール  |          2600オール | # 平和ツモのみ
|  30 |  500オール(1500) |  1000オール(2900) |  2000オール (5800)  | 3900オール(11600)*1 | # *1 ルールによっては満貫
|  40 |  700オール(2000) |  1300オール(3900) |  2600オール (7700)  |                満貫 |
|  50 |  800オール(2400) |  1600オール(4800) |  3200オール (9600)  |                満貫 |
|  60 | 1000オール(2900) |  2000オール(5800) | 3900オール(11600)*1 |                満貫 | # *1 ルールによっては満貫
|  70 | 1200オール(3400) |  2300オール(6800) |                満貫 |                満貫 |
|  80 | 1300オール(3900) |  2600オール(7700) |                満貫 |                満貫 |
|  90 | 1500オール(4400) |  2900オール(8700) |                満貫 |                満貫 |
| 100 | 1600オール(4800) |  3200オール(9600) |                満貫 |                満貫 |
| 110 | 1800オール(5300) | 3600オール(10600) |                満貫 |                満貫 |


親子
本場
自風
場風
ドラ
"""
