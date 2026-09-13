"""CLI color styling for prompt_toolkit components."""

from prompt_toolkit.styles import Style

# 统一 CLI 主题与组件样式
CLI_STYLE = Style.from_dict({
    # 基础输入与状态栏
    "prompt": "#ansicyan bold",
    "input": "#ffffff",
    "rprompt": "#ansigreen italic",
    "border": "#ansibrightblack",
    "bottom-toolbar": "noreverse bg:default",
    "statusbar": "#7f848e",

    # 菜单与弹窗通用
    "title": "#61afef bold",
    "menu-title": "#61afef bold",
    "item": "#abb2bf",
    "menu-item": "#abb2bf",
    "item-selected": "#98c379 bold",
    "menu-selected": "#98c379 bold",
    "menu-dim": "#5c6370 italic",
    "hint": "#5c6370 italic",
    "desc": "#5c6370 italic",
    "current-tag": "#e5c07b italic",
    "scroll-indicator": "#5c6370 italic",

    # 单选与多选标记
    "radio-checked": "#98c379 bold",
    "radio-unchecked": "#5c6370",
    "checkbox-checked": "#98c379 bold",
    "checkbox-unchecked": "#5c6370",

    # 补全菜单与滚动条
    "completion-menu": "bg:default fg:default",
    "completion-menu.completion": "noinherit bg:default fg:#7f848e",
    "completion-menu.completion.current": "noinherit noreverse bg:default fg:#98c379 bold",
    "completion-menu.meta.completion": "noinherit bg:default fg:#5c6370",
    "completion-menu.meta.completion.current": "noinherit noreverse bg:default fg:#98c379",
    "scrollbar": "noinherit bg:default",
})

# 向后兼容别名
RADIO_STYLE = CLI_STYLE
CHECKBOX_STYLE = CLI_STYLE
MENU_STYLE = CLI_STYLE
