import os
import shutil
import re
from typing import Optional
from wcwidth import wcwidth, wcswidth

ANSI_ESCAPE_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    """去除字符串中的 ANSI 转义控制码"""
    return ANSI_ESCAPE_RE.sub("", text)


def get_terminal_width(fallback: int = 80, min_width: int = 50, max_width: Optional[int] = None) -> int:
    """
    获取当前终端列宽（自适应 Windows / Linux / macOS）。
    动态调用 shutil.get_terminal_size()，每次调用获取实时窗口尺寸。
    """
    try:
        size = shutil.get_terminal_size(fallback=(fallback, 24))
        width = size.columns
    except Exception:
        width = fallback

    if width <= 0:
        width = fallback

    if min_width is not None and width < min_width:
        width = min_width
    if max_width is not None and width > max_width:
        width = max_width

    return width


def is_compact_terminal(threshold: int = 90) -> bool:
    """是否属于紧凑/窄终端视图"""
    return get_terminal_width() < threshold


def display_width(text: str) -> int:
    """
    计算文本在终端中的视觉显示列宽（考虑全角/中文/Emoji字符与 ANSI 码）。
    """
    plain = strip_ansi(text)
    w = wcswidth(plain)
    if w < 0:
        total = 0
        for char in plain:
            cw = wcwidth(char)
            total += cw if cw > 0 else 0
        return total
    return w


def truncate_to_width(text: str, max_w: int, ellipsis: str = "...") -> str:
    """
    按照视觉宽度截断文本，超出部分以 ellipsis 结尾。
    支持中文字符、Emoji 和半角符号安全截断。
    """
    if max_w <= 0:
        return ""

    plain = strip_ansi(text)
    if display_width(plain) <= max_w:
        return text

    ellipsis_w = display_width(ellipsis)
    if max_w <= ellipsis_w:
        target_w = max_w
        res = []
        cur_w = 0
        for ch in plain:
            cw = max(0, wcwidth(ch))
            if cur_w + cw > target_w:
                break
            res.append(ch)
            cur_w += cw
        return "".join(res)

    target_w = max_w - ellipsis_w
    res = []
    cur_w = 0
    for ch in plain:
        cw = max(0, wcwidth(ch))
        if cur_w + cw > target_w:
            break
        res.append(ch)
        cur_w += cw

    return "".join(res) + ellipsis


def pad_to_width(text: str, width: int, align: str = "left", fillchar: str = " ") -> str:
    """
    根据视觉显示宽度进行填充对齐（'left', 'right', 'center'）。
    """
    cur_w = display_width(text)
    if cur_w >= width:
        return text

    missing = width - cur_w
    fill_w = max(1, display_width(fillchar))
    fill_count = missing // fill_w

    if align == "right":
        return (fillchar * fill_count) + text
    elif align == "center":
        left_count = fill_count // 2
        right_count = fill_count - left_count
        return (fillchar * left_count) + text + (fillchar * right_count)
    else:
        return text + (fillchar * fill_count)


def fit_box_line(
    content: str,
    inner_width: int,
    left_border: str = "│ ",
    right_border: str = " │",
    ellipsis: str = "...",
) -> str:
    """
    将单行内容安全适配进指定内宽的盒子，超出自动截断，不足自动留白。
    """
    content_truncated = truncate_to_width(content, inner_width, ellipsis=ellipsis)
    padded = pad_to_width(content_truncated, inner_width)
    return f"{left_border}{padded}{right_border}\n"


def build_box_header(title: str, box_width: int, left_corner: str = "╭─ ", right_corner: str = " ─╮") -> str:
    """
    生成带标题的自适应顶部边框，标题若超长则智能截断。
    """
    fixed_w = display_width(left_corner) + display_width(right_corner)
    available_for_title = max(0, box_width - fixed_w)
    fit_title = truncate_to_width(title, available_for_title)

    remaining_w = box_width - display_width(left_corner) - display_width(fit_title) - display_width(right_corner)
    if remaining_w < 0:
        remaining_w = 0
    dash_count = remaining_w
    return f"{left_corner}{fit_title}{'─' * dash_count}{right_corner}\n"


def build_box_footer(box_width: int, left_corner: str = "╰", right_corner: str = "╯") -> str:
    """生成自适应底部边框"""
    dash_len = max(0, box_width - display_width(left_corner) - display_width(right_corner))
    return f"{left_corner}{'─' * dash_len}{right_corner}"
