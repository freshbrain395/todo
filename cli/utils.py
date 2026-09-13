"""CLI utility functions for terminal display, width calculations, and string formatting."""

import re
import shutil
import unicodedata


def strip_ansi(text: str) -> str:
    """去除 ANSI 颜色控制转义字符"""
    ansi_regex = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_regex.sub("", text)


def display_width(text: str) -> int:
    """计算文本在终端中占用的实际列宽 (支持中英文、Emoji 等全角半角计算)"""
    clean = strip_ansi(text)
    w = 0
    for ch in clean:
        if unicodedata.east_asian_width(ch) in ("F", "W"):
            w += 2
        else:
            w += 1
    return w


def truncate_to_width(text: str, max_w: int, ellipsis: str = "…") -> str:
    """按照终端显示列宽截断文本，超出部分附加省略号"""
    if display_width(text) <= max_w:
        return text
    el_w = display_width(ellipsis)
    target = max_w - el_w
    if target <= 0:
        return ellipsis[:max_w]
    res = []
    curr_w = 0
    for ch in text:
        ch_w = 2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1
        if curr_w + ch_w > target:
            break
        res.append(ch)
        curr_w += ch_w
    return "".join(res) + ellipsis


def pad_to_width(text: str, width: int, align: str = "left") -> str:
    """按终端显示宽度对文本进行空格填充对齐 (left, right, center)"""
    curr_w = display_width(text)
    if curr_w >= width:
        return text
    pad = width - curr_w
    if align == "center":
        left = pad // 2
        right = pad - left
        return " " * left + text + " " * right
    elif align == "right":
        return " " * pad + text
    return text + " " * pad


def get_terminal_width(fallback: int = 80) -> int:
    """动态获取当前终端窗口的列宽"""
    return shutil.get_terminal_size((fallback, 20)).columns


def get_terminal_height(fallback: int = 24) -> int:
    """动态获取当前终端窗口的行数"""
    return shutil.get_terminal_size((80, fallback)).lines


def get_border(cols: int | None = None) -> str:
    """动态获取终端列宽，生成横线"""
    width = cols or get_terminal_width(80)
    return "─" * max(20, width - 2)
