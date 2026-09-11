"""CLI color styling for prompt_toolkit components."""

from prompt_toolkit.styles import Style

# 纯无背景色、全灰色字体样式，补全菜单完全融入终端背景，选中项仅改变前景色
CLI_STYLE = Style.from_dict({
    "bottom-toolbar": "noreverse noinherit bg:default fg:#7f848e",
    "toolbar-gray": "noreverse noinherit bg:default fg:#7f848e",
    "menu-title": "#61afef bold",
    "menu-selected": "#98c379 bold",
    "menu-item": "#abb2bf",
    "menu-dim": "#5c6370",
    # prompt_toolkit 补全菜单样式：纯透明无背景，普通项灰色，当前选中项绿色加粗
    "completion-menu": "bg:default fg:default",
    "completion-menu.completion": "noinherit bg:default fg:#7f848e",
    "completion-menu.completion.current": "noinherit noreverse bg:default fg:#98c379 bold",
    "completion-menu.meta.completion": "noinherit bg:default fg:#5c6370",
    "completion-menu.meta.completion.current": "noinherit noreverse bg:default fg:#98c379",
    "scrollbar": "noinherit bg:default",
    "scrollbar.background": "noinherit bg:default",
    "scrollbar.button": "noinherit bg:default",
    "scrollbar.arrow": "noinherit bg:default",
    "scrollbar.start": "noinherit bg:default nounderline",
    "scrollbar.end": "noinherit bg:default nounderline",
    # 输入框 (Boxed Input) 样式
    "frame": "noinherit bg:default",
    "frame.border": "#5c6370",
    "frame.label": "#61afef bold",
    "placeholder": "#5c6370 italic",
})
