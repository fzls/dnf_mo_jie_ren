import ctypes
import math
import os.path
import time

import win32api
from pynput import keyboard, mouse

from data_struct import ConfigInterface
from draw import draw_line_async, Point
from log import logger, color
from util import show_head_line

STEP_START = "选择起始点"
STEP_END = "选择终点"


# 计算下一步是什么
def get_next_step(current_step: str) -> str:
    next_step = STEP_END
    if current_step == STEP_START:
        next_step = STEP_END
    elif current_step == STEP_END:
        next_step = STEP_START
    else:
        raise AssertionError(f"unexpected step {current_step}")

    return next_step


class Config(ConfigInterface):
    def __init__(self):
        # 由于实际分辨率问题，按照像素计算出来，可能与实际的有区别，这里用一个系数自行调整，使其能恰好跳到目标点
        # 如果跳的过远，就把这个数值调小点。太近了，则调大，直到找到一个在当前设置下比较合适的数目
        self.adjustment_coefficient = 1.05


def load_config() -> Config:
    cfg = Config()
    cfg.load_from_json_file(config_path())
    return cfg


def save_config(cfg: Config):
    save_path = config_path()
    make_sure_dir_exists(os.path.dirname(save_path))

    cfg.save_to_json_file(save_path)


def make_sure_dir_exists(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)


def config_path() -> str:
    return os.path.join(os.path.expandvars("%APPDATA%"), "mo_jie_ren", "config.json")


def ensure_get_actual_position():
    # 确保不受缩放影响，保证Controller获取的坐标是物理屏幕坐标
    # 参考：https://pynput.readthedocs.io/en/latest/mouse.html#ensuring-consistent-coordinates-between-listener-and-controller-on-windows
    PROCESS_PER_MONITOR_DPI_AWARE = 2
    ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)


def disable_quick_edit_mode():
    # https://docs.microsoft.com/en-us/windows/console/setconsolemode
    ENABLE_EXTENDED_FLAGS = 0x0080

    logger.info(color("bold_green") + "将禁用命令行的快速编辑模式，避免鼠标误触时程序暂停")
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(win32api.STD_INPUT_HANDLE), ENABLE_EXTENDED_FLAGS)


def main():
    # disable_quick_edit_mode()
    cfg = load_config()

    ensure_get_actual_position()

    mouseController = mouse.Controller()

    show_head_line("""
使用说明
请参考在线文档： *********************************
    """.strip(), )

    current_step = STEP_START
    current_block = 1
    start_position = Point(0, 0)
    end_position = Point(0, 0)
    actual_position = Point(0, 0)

    bounce_force = 100
    base_bounce_force = 100

    def show_step_prompt():
        if current_step == STEP_START:
            logger.info("")
            logger.info(color("bold_yellow") + f"当前开始第 {current_block} 个格子，请依次将鼠标放到当前位置和目标位置，并分别点击 左ctrl 键（键盘左下角那个）(停止使用可以点击右上角关闭）")

        logger.info(color("bold_yellow") + f"当前步骤为 {current_step}")

    logger.info(f"当前调整系数为 {cfg.adjustment_coefficient}")

    show_step_prompt()

    with keyboard.Events() as events:
        for event in events:
            if type(event) != keyboard.Events.Press:
                continue

            if event.key == keyboard.Key.ctrl_l:
                x, y = mouseController.position

                if current_step == STEP_START:
                    start_position = Point(x, y)
                    logger.info(f"起点为 {start_position}")
                elif current_step == STEP_END:
                    end_position = Point(x, y)

                    delta_x = end_position.x - start_position.x
                    logger.info(f"目标为 {end_position}")
                    logger.info(f"X 差值为 {delta_x}")

                    # 计算需要按住的时间
                    # 游戏中设定的x速度
                    speed_x_per_second = 300
                    # 考虑弹跳力的情况
                    actual_speed = speed_x_per_second * bounce_force / base_bounce_force
                    press_seconds = cfg.adjustment_coefficient * math.fabs(delta_x) / actual_speed

                    logger.info(color("bold_green") + f"预计需要按住左键 {press_seconds} 秒 (实际速度={actual_speed} 基础速度={speed_x_per_second} 弹跳力={bounce_force} 最终调整系数={cfg.adjustment_coefficient})")

                    # 画条线标记下
                    draw_line_async(start_position, end_position, press_seconds)

                    # 点击对应时长
                    mouseController.press(mouse.Button.left)
                    time.sleep(press_seconds)
                    mouseController.release(mouse.Button.left)

                    if bounce_force != base_bounce_force:
                        bounce_force = base_bounce_force
                        logger.info("弹跳力重置为默认值")
                else:
                    raise AssertionError()

                # 更新步骤和区块
                current_step = get_next_step(current_step)
                if current_step == STEP_START:
                    current_block += 1

                show_step_prompt()
            elif event.key == keyboard.KeyCode.from_char("z"):
                bounce_force = 90
                logger.info(color("bold_cyan") + f"本轮弹跳力调整为{bounce_force}")
            elif event.key == keyboard.KeyCode.from_char("c"):
                bounce_force = 110
                logger.info(color("bold_cyan") + f"本轮弹跳力调整为{bounce_force}")
            elif event.key == keyboard.KeyCode.from_char("x"):
                bounce_force = 100
                logger.info(color("bold_cyan") + f"本轮弹跳力重置为{bounce_force}")
            elif event.key == keyboard.Key.caps_lock:
                logger.info(color("bold_green") + "进入修正 调整系数 模式，并重置本轮步骤为 选择起始点 阶段，请按照提示输入新的系数~")

                current_step = STEP_START
                time.sleep(0.5)

                new_coefficient = 1.0
                while True:
                    try:
                        new_coefficient = float(input(f"当前调整系数为 {cfg.adjustment_coefficient}，请输入新的系数（如果跳太远，就填个小点的数，跳太近则填个大点的数）: "))
                        break
                    except Exception as e:
                        logger.error(color("bold_yellow") + "输入的不是一个数字，请确保输入的是浮点数")


                old = cfg.adjustment_coefficient
                cfg.adjustment_coefficient = float(new_coefficient)
                logger.info(color("bold_yellow") + f"系数变更为 {cfg.adjustment_coefficient}，之前为 {old}，将保存到用户目录的配置")
                save_config(cfg)

                show_step_prompt()


if __name__ == '__main__':
    main()
