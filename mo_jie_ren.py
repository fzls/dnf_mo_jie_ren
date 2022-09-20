import ctypes
import math
import time

from pynput import keyboard, mouse

from draw import draw_line_async, Point

# 确保不受缩放影响，保证Controller获取的坐标是物理屏幕坐标
# 参考：https://pynput.readthedocs.io/en/latest/mouse.html#ensuring-consistent-coordinates-between-listener-and-controller-on-windows
PROCESS_PER_MONITOR_DPI_AWARE = 2
ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)

mouseController = mouse.Controller()

prompt_message = "请依次将鼠标放到当前位置和目标位置，并分别点击 左ctrl 键（键盘左下角那个）"

print(prompt_message)

bounce_force = 100
base_bounce_force = 100
print("如何调整当次的弹跳力：z=90 c=110，当吃到对应buff时请点击对应键即可，误触按x直接重置回100即可")

index = 0
start_position = Point(0, 0)
end_position = Point(0, 0)
with keyboard.Events() as events:
    for event in events:
        if type(event) != keyboard.Events.Press:
            continue

        if event.key == keyboard.Key.ctrl_l:
            # 奇数表示开始位置，偶数表示结束位置
            index += 1

            x, y = mouseController.position
            if index % 2 == 1:
                start_position = Point(x, y)
                print(f"\t起点为 {start_position}")
            else:
                end_position = Point(x, y)

                delta_x = end_position.x - start_position.x
                print(f"\t目标为 {end_position}")
                print(f"\tx差值为 {delta_x}")

                # 计算需要按住的时间
                # 游戏中设定的x速度
                speed_x_per_second = 300
                # 考虑弹跳力的情况
                actual_speed = speed_x_per_second * bounce_force / base_bounce_force
                # 由于实际分辨率问题，按照像素计算出来，可能与实际的有区别，这里用一个系数自行调整，使其能恰好跳到目标点
                # 如果跳的过远，就把这个数值调小点。太近了，则调大，直到找到一个在当前设置下比较合适的数目
                addjustment_coefficient = 1.188
                press_seconds = addjustment_coefficient * math.fabs(delta_x) / actual_speed

                print(f"\t预计需要按住左键 {press_seconds} 秒 (实际速度={actual_speed} 基础速度={speed_x_per_second} 弹跳力={bounce_force} 最终调整系数={addjustment_coefficient})")

                draw_line_async(start_position, end_position, press_seconds)

                mouseController.press(mouse.Button.left)
                time.sleep(press_seconds)
                mouseController.release(mouse.Button.left)

                if bounce_force != base_bounce_force:
                    bounce_force = base_bounce_force
                    print("\t弹跳力重置为默认值")

                print(prompt_message)
        elif event.key == keyboard.KeyCode.from_char("z"):
            bounce_force = 90
            print(f"本轮弹跳力调整为{bounce_force}")
        elif event.key == keyboard.KeyCode.from_char("c"):
            bounce_force = 110
            print(f"本轮弹跳力调整为{bounce_force}")
        elif event.key == keyboard.KeyCode.from_char("x"):
            bounce_force = 100
            print(f"本轮弹跳力重置为{bounce_force}")
