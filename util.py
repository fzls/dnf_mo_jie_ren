from typing import Tuple

from log import color, logger, asciiReset


def show_head_line(msg, msg_color="", max_line_content_width=80, min_line_printed_width=80):
    msg_color = msg_color or color("fg_bold_green")

    msg = split_line_if_too_long(msg, max_line_content_width)
    line_width = max(min_line_printed_width, get_max_line_width(msg))

    # 按照下列格式打印
    # ┌──────────┐
    # │   test   │
    # │   test   │
    # │   test   │
    # └──────────┘
    logger.warning("┌" + "─" + "─" * line_width + "┐")
    for line in msg.splitlines():
        logger.warning("│" + " " + msg_color + padLeftRight(line, line_width) + asciiReset + color("WARNING") + "│")
    logger.warning("└" + "─" + "─" * line_width + "┘")


def split_line_if_too_long(msg: str, max_line_width) -> str:
    # 确保每行不超过指定大小，超过的行分割为若干个符合条件的行，并在末尾增加\n来标记
    padding = "\\n"
    padding_width = printed_width(padding)

    lines = []
    for line in msg.splitlines():
        while printed_width(line) > max_line_width:
            fitted_line, line = split_by_printed_width(line, max_line_width - padding_width)
            lines.append(fitted_line + padding)

        lines.append(line)

    return "\n".join(lines)


def get_max_line_width(msg: str) -> int:
    line_length = 0
    for line in msg.splitlines():
        line_length = max(line_length, printed_width(line))

    return line_length


def padLeftRight(msg, target_size, pad_char=" ", mode="middle", need_truncate=False):
    msg = str(msg)
    if need_truncate:
        msg = truncate(msg, target_size)
    msg_len = printed_width(msg)
    pad_left_len, pad_right_len = 0, 0
    if msg_len < target_size:
        total = target_size - msg_len
        pad_left_len = total // 2
        pad_right_len = total - pad_left_len

    if mode == "middle":
        return pad_char * pad_left_len + msg + pad_char * pad_right_len
    elif mode == "left":
        return msg + pad_char * (pad_left_len + pad_right_len)
    else:
        return pad_char * (pad_left_len + pad_right_len) + msg


def printed_width(msg):
    return sum(1 if ord(c) < 128 else 2 for c in msg)


def split_by_printed_width(msg: str, expect_width: int) -> Tuple[str, str]:
    if printed_width(msg) <= expect_width:
        return msg, ""

    index = 0
    current_width = 0
    for substr in msg:
        current_width += printed_width(substr)
        if current_width > expect_width:
            break
        index += len(substr)

    return msg[:index], msg[index:]


def truncate(msg, expect_width) -> str:
    if printed_width(msg) <= expect_width:
        return msg

    truncated = []
    current_width = 3
    for substr in msg:
        current_width += printed_width(substr)
        if current_width > expect_width:
            truncated.append("...")
            break
        truncated.append(substr)

    return "".join(truncated)
