import threading
import time
from collections import namedtuple

import wx

Point = namedtuple('Point', ['x', 'y'])


def draw_line(start_point: Point, end_point: Point, duration_seconds: float):
    # init
    app = wx.App()
    dc = wx.ScreenDC()

    # set line and fill style
    dc.SetBrush(wx.TRANSPARENT_BRUSH)
    dc.SetPen(wx.Pen((255, 0, 0), width=3, style=wx.PENSTYLE_SOLID))

    start_time = time.time()
    while True:
        dc.DrawLine(start_point.x, start_point.y, end_point.x, end_point.y)

        if time.time() - start_time >= duration_seconds:
            break


def draw_line_async(start_point: Point, end_point: Point, duration_seconds: float):
    threading.Thread(target=draw_line, args=(start_point, end_point, duration_seconds), daemon=True).start()


if __name__ == '__main__':
    start = Point(1920, 540)
    end = Point(start.x + 500, start.y + 500)

    draw_line(start, end, 2)
