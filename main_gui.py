import sys
import os
import datetime
import sqlite3
import signal
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QLineEdit,
    QComboBox, QDialog, QDateTimeEdit, QMenu, QSystemTrayIcon,
    QFrame, QCheckBox, QTextEdit, QStatusBar, QMessageBox,
    QGraphicsDropShadowEffect, QSplitter, QHeaderView, QSizePolicy,
    QDialogButtonBox, QSpinBox
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QDateTime, QTimer, QSize, QRectF
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QColor, QFont, QAction, QPainter, QPainterPath, QBrush, QPen, QFontMetrics
)

# 引入现有后端核心模块
from db_manager import TodoDatabase
from reminder_scheduler import global_reminder_scheduler, show_desktop_notification
from llm_client import (
    load_config, save_config, NativeOllamaLLM, SiliconFlowLLM,
    parse_user_intent, prompt_select_llm
)
from mode_config import (
    get_mode_config, list_all_modes, build_mode_messages
)

# =====================================================================
# 1. 多主题 QSS 样式表配置 (Themes Registry)
# =====================================================================

LIGHT_QSS = """
QWidget {
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 13px;
    color: #2D3748;
}
QMainWindow, QDialog {
    background-color: #F7FAFC;
}
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #2D3748;
    selection-background-color: #EDF2F7;
    selection-color: #1A202C;
    border: 1px solid #CBD5E0;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}
QComboBox QAbstractItemView::item {
    min-height: 26px;
    border-radius: 4px;
    padding: 3px 8px;
}
QLineEdit:disabled, QComboBox:disabled {
    background-color: #EDF2F7;
    color: #A0AEC0;
}
QLineEdit, QDateTimeEdit {
    background-color: #FFFFFF;
    color: #2D3748;
    border: 1px solid #CBD5E0;
    border-radius: 6px;
    padding: 5px 10px;
    outline: none;
}
QLineEdit:focus, QDateTimeEdit:focus {
    border: 2px solid #3182CE;
}
QComboBox {
    background-color: #FFFFFF;
    color: #2D3748;
    border: 1px solid #CBD5E0;
    border-radius: 6px;
    padding: 5px 26px 5px 10px;
    outline: none;
}
QComboBox:focus {
    border: 2px solid #3182CE;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border: none;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
    background-color: transparent;
}
QComboBox::down-arrow {
    image: url(data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="%23718096" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>);
    width: 10px;
    height: 10px;
}
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}
QFrame#aiInputFrame {
    background-color: #FFFFFF;
    border-top: 1px solid #E2E8F0;
}
QStatusBar {
    background-color: #FFFFFF;
    color: #718096;
    border-top: 1px solid #E2E8F0;
}
QFrame#todoCard {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    margin: 3px 6px;
}
QFrame#todoCard:hover {
    border-color: #CBD5E0;
    background-color: #F8FAFC;
}
"""

DARK_QSS = """
QWidget {
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 13px;
    color: #C0CAF5;
}
QMainWindow, QDialog {
    background-color: #1A1B26;
}
QComboBox QAbstractItemView {
    background-color: #1F2335;
    color: #C0CAF5;
    selection-background-color: #24283B;
    selection-color: #7AA2F7;
    border: 1px solid #414868;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}
QComboBox QAbstractItemView::item {
    min-height: 26px;
    border-radius: 4px;
    padding: 3px 8px;
}
QLineEdit:disabled, QComboBox:disabled {
    background-color: #16161E;
    color: #565F89;
}
QLineEdit, QDateTimeEdit {
    background-color: #1F2335;
    color: #C0CAF5;
    border: 1px solid #414868;
    border-radius: 6px;
    padding: 5px 10px;
    outline: none;
}
QLineEdit:focus, QDateTimeEdit:focus {
    border: 2px solid #7AA2F7;
}
QComboBox {
    background-color: #1F2335;
    color: #C0CAF5;
    border: 1px solid #414868;
    border-radius: 6px;
    padding: 5px 26px 5px 10px;
    outline: none;
}
QComboBox:focus {
    border: 2px solid #7AA2F7;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border: none;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
    background-color: transparent;
}
QComboBox::down-arrow {
    image: url(data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="%23A9B1D6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>);
    width: 10px;
    height: 10px;
}
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}
QFrame#aiInputFrame {
    background-color: #24283B;
    border-top: 1px solid #414868;
}
QStatusBar {
    background-color: #24283B;
    color: #A9B1D6;
    border-top: 1px solid #414868;
}
QFrame#todoCard {
    background-color: #24283B;
    border: 1px solid #414868;
    border-radius: 8px;
    margin: 3px 6px;
}
QFrame#todoCard:hover {
    border-color: #7AA2F7;
    background-color: #1F2335;
}
"""

NORD_QSS = """
QWidget {
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 13px;
    color: #E5E9F0;
}
QMainWindow, QDialog {
    background-color: #2E3440;
}
QComboBox QAbstractItemView {
    background-color: #3B4252;
    color: #E5E9F0;
    selection-background-color: #434C5E;
    selection-color: #88C0D0;
    border: 1px solid #4C566A;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}
QComboBox QAbstractItemView::item {
    min-height: 26px;
    border-radius: 4px;
    padding: 3px 8px;
}
QLineEdit:disabled, QComboBox:disabled {
    background-color: #242933;
    color: #4C566A;
}
QLineEdit, QDateTimeEdit {
    background-color: #3B4252;
    color: #E5E9F0;
    border: 1px solid #4C566A;
    border-radius: 6px;
    padding: 5px 10px;
    outline: none;
}
QLineEdit:focus, QDateTimeEdit:focus {
    border: 2px solid #88C0D0;
}
QComboBox {
    background-color: #3B4252;
    color: #E5E9F0;
    border: 1px solid #4C566A;
    border-radius: 6px;
    padding: 5px 26px 5px 10px;
    outline: none;
}
QComboBox:focus {
    border: 2px solid #88C0D0;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border: none;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
    background-color: transparent;
}
QComboBox::down-arrow {
    image: url(data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="%23D8DEE9" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>);
    width: 10px;
    height: 10px;
}
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}
QFrame#aiInputFrame {
    background-color: #3B4252;
    border-top: 1px solid #4C566A;
}
QStatusBar {
    background-color: #3B4252;
    color: #D8DEE9;
    border-top: 1px solid #4C566A;
}
QFrame#todoCard {
    background-color: #3B4252;
    border: 1px solid #4C566A;
    border-radius: 8px;
    margin: 3px 6px;
}
QFrame#todoCard:hover {
    border-color: #88C0D0;
    background-color: #434C5E;
}
"""

THEMES = {
    "light": LIGHT_QSS,
    "dark": DARK_QSS,
    "nord": NORD_QSS
}

# =====================================================================
# 2. 线程安全子线程 (QThread Workers)
# =====================================================================

class DbWorker(QThread):
    """通用数据库操作工作线程，防止 SQLite 阻塞主 UI"""
    finished_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)

    def __init__(self, func, *args, db_path="todos.db", **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.db_path = db_path

    def run(self):
        try:
            # 在子线程内建立独立的 SQLite 连接句柄
            db = TodoDatabase(self.db_path)
            func_name = getattr(self.func, '__name__', '')
            db_method = getattr(db, func_name, None)
            
            if db_method is not None and getattr(db_method, '__func__', None) == self.func:
                res = db_method(*self.args, **self.kwargs)
            elif callable(self.func):
                try:
                    res = self.func(db, *self.args, **self.kwargs)
                except TypeError:
                    res = self.func(*self.args, **self.kwargs)
            else:
                raise ValueError("传递给 DbWorker 的任务不可调用")

            self.finished_signal.emit(res)
        except Exception as e:
            self.error_signal.emit(str(e))


class AIAgentWorker(QThread):
    """AI 自然语言意图解析与执行工作线程"""
    result_signal = pyqtSignal(str, bool)  # message, should_refresh

    def __init__(self, user_text: str, config: Dict[str, Any], db_path: str = "todos.db"):
        super().__init__()
        self.user_text = user_text
        self.config = config
        self.db_path = db_path

    def run(self):
        try:
            # 1. 实例化 LLM 客户端
            provider = self.config.get("provider", "siliconflow")
            model = self.config.get("model", "deepseek-ai/DeepSeek-V4-Flash")
            api_key = self.config.get("siliconflow_api_key", "")
            base_url = self.config.get("base_url", "")
            enable_thinking = self.config.get("enable_thinking", False)

            if provider == "siliconflow":
                kwargs = {"api_key": api_key, "model": model, "enable_thinking": enable_thinking}
                if base_url:
                    kwargs["host"] = base_url
                llm = SiliconFlowLLM(**kwargs)
            else:
                kwargs = {"model": model, "enable_thinking": enable_thinking}
                if base_url:
                    kwargs["host"] = base_url
                llm = NativeOllamaLLM(**kwargs)

            # 2. 调用意图解析器
            parsed = parse_user_intent(self.user_text, llm)
            action = parsed.get("action")
            data = parsed.get("data", {})

            db = TodoDatabase(self.db_path)

            if action == "add":
                title = data.get("title", self.user_text)
                priority = data.get("priority", "medium")
                category = data.get("category", "工作")
                remind_at = data.get("remind_at")
                todo_id = db.add_todo(title, priority, category, remind_at)

                if remind_at:
                    try:
                        remind_dt = datetime.datetime.strptime(remind_at, "%Y-%m-%d %H:%M:%S")
                        delay = (remind_dt - datetime.datetime.now()).total_seconds()
                        if delay > 0:
                            global_reminder_scheduler.schedule_reminder(todo_id, title, delay)
                    except Exception:
                        pass
                msg = f"✨ 成功理解意图并创建待办事项：[{title}] (分类: {category}, 优先级: {priority})"
                self.result_signal.emit(msg, True)

            elif action == "complete":
                todo_id = data.get("id")
                if todo_id and db.complete_todo(todo_id):
                    global_reminder_scheduler.cancel_reminder(todo_id)
                    self.result_signal.emit(f"✅ 成功完成待办事项 ID [{todo_id}]", True)
                else:
                    self.result_signal.emit("⚠️ 未找到对应的待办事项或操作失败", False)

            elif action == "delete":
                todo_id = data.get("id")
                if todo_id and db.delete_todo(todo_id):
                    global_reminder_scheduler.cancel_reminder(todo_id)
                    self.result_signal.emit(f"🗑️ 成功删除待办事项 ID [{todo_id}]", True)
                else:
                    self.result_signal.emit("⚠️ 删除失败，未找到该任务", False)

            elif action == "query":
                todos = db.query_sql("SELECT * FROM todos WHERE completed = 0 ORDER BY id DESC LIMIT 5")
                summary = "📋 当前未完成的前5个待办事项：\n"
                for t in todos:
                    summary += f"- [{t['id']}] {t['title']} ({t['priority']} | {t['category']})\n"
                self.result_signal.emit(summary, False)

            else:
                self.result_signal.emit(f"💬 AI 回复：{parsed.get('raw_response', '我已收到您的输入。')}", False)

        except Exception as e:
            self.result_signal.emit(f"❌ AI 引擎处理异常: {str(e)}", False)


# =====================================================================
# 3. 自定义任务卡片 Item Widget
# =====================================================================

class TodoItemWidget(QFrame):
    """单个待办事项现代化外观卡片"""
    status_changed = pyqtSignal(int, bool)  # todo_id, is_completed
    delete_requested = pyqtSignal(int)      # todo_id
    edit_requested = pyqtSignal(dict)        # todo_data

    def __init__(self, todo_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.todo_data = todo_data
        self.init_ui()

    def init_ui(self):
        self.setObjectName("todoCard")
        self.setStyleSheet("""
            QFrame#todoCard {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                margin: 3px 6px;
            }
            QFrame#todoCard:hover {
                border-color: #CBD5E0;
                background-color: #F8FAFC;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # 1. 完成状态复选框
        self.check_box = QCheckBox()
        self.check_box.setChecked(bool(self.todo_data.get("completed", 0)))
        self.check_box.toggled.connect(self._on_toggled)
        layout.addWidget(self.check_box)

        # 2. 标题与属性列
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # 标题 Label
        title_text = self.todo_data.get("title", "")
        self.title_label = QLabel(title_text)
        self.title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        
        if self.check_box.isChecked():
            self.title_label.setStyleSheet("color: #A0AEC0; text-decoration: line-through;")
        else:
            self.title_label.setStyleSheet("color: #1A202C; text-decoration: none;")
            
        info_layout.addWidget(self.title_label)

        # 细项标签栏（分类 + 优先级 + 提醒时间）
        badge_layout = QHBoxLayout()
        badge_layout.setSpacing(8)

        # 分类 Badge
        cat = self.todo_data.get("category", "工作")
        cat_label = QLabel(f"🏷️ {cat}")
        cat_label.setStyleSheet("""
            background-color: #EDF2F7;
            color: #4A5568;
            border-radius: 4px;
            padding: 1px 6px;
            font-size: 11px;
        """)
        badge_layout.addWidget(cat_label)

        # 优先级 Badge
        prio = self.todo_data.get("priority", "medium").lower()
        prio_map = {
            "high": ("🔴 高优", "#FFF5F5", "#C53030"),
            "medium": ("🟡 中优", "#FEFCBF", "#975A16"),
            "low": ("🔵 低优", "#EBF8FF", "#2B6CB0")
        }
        prio_text, prio_bg, prio_fg = prio_map.get(prio, ("🟡 中优", "#FEFCBF", "#975A16"))
        prio_label = QLabel(prio_text)
        prio_label.setStyleSheet(f"""
            background-color: {prio_bg};
            color: {prio_fg};
            border-radius: 4px;
            padding: 1px 6px;
            font-size: 11px;
            font-weight: bold;
        """)
        badge_layout.addWidget(prio_label)

        # 定时提醒标记
        remind_at = self.todo_data.get("remind_at")
        if remind_at:
            remind_label = QLabel(f"⏰ {remind_at}")
            remind_label.setStyleSheet("""
                color: #DD6B20;
                font-size: 11px;
                font-weight: 500;
            """)
            badge_layout.addWidget(remind_label)

        badge_layout.addStretch()
        info_layout.addLayout(badge_layout)

        layout.addLayout(info_layout, stretch=1)

        # 3. 悬浮操作按钮栏
        self.btn_edit = QPushButton("编辑")
        self.btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_edit.setStyleSheet("padding: 3px 8px; font-size: 12px;")
        self.btn_edit.clicked.connect(lambda: self.edit_requested.emit(self.todo_data))
        layout.addWidget(self.btn_edit)

        self.btn_del = QPushButton("🗑️")
        self.btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_del.setStyleSheet("padding: 3px 8px; font-size: 12px; color: #E53E3E;")
        self.btn_del.clicked.connect(lambda: self.delete_requested.emit(self.todo_data["id"]))
        layout.addWidget(self.btn_del)

    def _on_toggled(self, checked: bool):
        if checked:
            self.title_label.setStyleSheet("color: #A0AEC0; text-decoration: line-through;")
        else:
            self.title_label.setStyleSheet("color: #1A202C; text-decoration: none;")
        self.status_changed.emit(self.todo_data["id"], checked)


# =====================================================================
# 4. 新建/编辑待办事项弹窗 (Dialog)
# =====================================================================

class AddEditTodoDialog(QDialog):
    """新建或编辑待办事项对话框"""

    def __init__(self, todo_data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.todo_data = todo_data or {}
        self.setWindowTitle("编辑待办事项" if todo_data else "添加新待办事项")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # 1. 标题输入
        layout.addWidget(QLabel("任务标题 *"))
        self.title_input = QLineEdit(self.todo_data.get("title", ""))
        self.title_input.setPlaceholderText("请输入待办事项内容...")
        layout.addWidget(self.title_input)

        # 2. 分类与优先级
        row1 = QHBoxLayout()
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("任务分类"))
        self.cat_input = QComboBox()
        self.cat_input.addItems(["工作", "个人", "学习", "健康", "财务", "其他"])
        curr_cat = self.todo_data.get("category", "工作")
        idx = self.cat_input.findText(curr_cat)
        if idx >= 0:
            self.cat_input.setCurrentIndex(idx)
        else:
            self.cat_input.setEditText(curr_cat)
        v1.addWidget(self.cat_input)
        row1.addLayout(v1)

        v2 = QVBoxLayout()
        v2.addWidget(QLabel("优先级"))
        self.prio_input = QComboBox()
        self.prio_input.addItem("🔴 高优 (high)", "high")
        self.prio_input.addItem("🟡 中优 (medium)", "medium")
        self.prio_input.addItem("🔵 低优 (low)", "low")
        curr_prio = self.todo_data.get("priority", "medium")
        prio_idx = {"high": 0, "medium": 1, "low": 2}.get(curr_prio, 1)
        self.prio_input.setCurrentIndex(prio_idx)
        v2.addWidget(self.prio_input)
        row1.addLayout(v2)

        layout.addLayout(row1)

        # 3. 定时提醒设置
        self.enable_reminder_cb = QCheckBox("设置定时提醒时间")
        layout.addWidget(self.enable_reminder_cb)

        self.datetime_input = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600))
        self.datetime_input.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.datetime_input.setCalendarPopup(True)
        self.datetime_input.setEnabled(False)
        layout.addWidget(self.datetime_input)

        self.enable_reminder_cb.toggled.connect(self.datetime_input.setEnabled)

        remind_at = self.todo_data.get("remind_at")
        if remind_at:
            dt = QDateTime.fromString(remind_at, "yyyy-MM-dd HH:mm:ss")
            if dt.isValid():
                self.datetime_input.setDateTime(dt)
                self.enable_reminder_cb.setChecked(True)

        # 4. 按钮操作栏
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setText("保存")
        btn_box.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        btn_box.accepted.connect(self._validate_and_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _validate_and_accept(self):
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "警告", "任务标题不能为空！")
            return
        self.accept()

    def get_data(self) -> Dict[str, Any]:
        remind_str = None
        if self.enable_reminder_cb.isChecked():
            remind_str = self.datetime_input.dateTime().toString("yyyy-MM-dd HH:mm:ss")

        return {
            "title": self.title_input.text().strip(),
            "category": self.cat_input.currentText(),
            "priority": self.prio_input.currentData(),
            "remind_at": remind_str
        }


class ModelConfigDialog(QDialog):
    """LLM 大模型提供商 (Provider)、Base URL、API Key 与 模型名称配置弹窗"""

    def __init__(self, config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.setWindowTitle("⚙️ 配置大语言模型 (LLM)")
        self.setMinimumWidth(460)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # 1. Provider 服务提供商选择
        layout.addWidget(QLabel("服务提供商 (Provider) *"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItem("SiliconFlow (硅基流动云端 API)", "siliconflow")
        self.provider_combo.addItem("Native Ollama (本地大模型)", "ollama")

        curr_provider = self.config.get("provider", "siliconflow")
        p_idx = 0 if curr_provider == "siliconflow" else 1
        self.provider_combo.setCurrentIndex(p_idx)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        layout.addWidget(self.provider_combo)

        # 2. Base URL
        layout.addWidget(QLabel("接口地址 (Base URL)"))
        curr_url = self.config.get("base_url", "https://api.siliconflow.cn/v1" if curr_provider == "siliconflow" else "http://localhost:11434")
        self.url_input = QLineEdit(curr_url)
        self.url_input.setPlaceholderText("例如: https://api.siliconflow.cn/v1 或 http://localhost:11434")
        layout.addWidget(self.url_input)

        # 3. API Key
        layout.addWidget(QLabel("API Key (密钥)"))
        self.key_input = QLineEdit(self.config.get("siliconflow_api_key", ""))
        self.key_input.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        self.key_input.setPlaceholderText("sk-...")
        self.key_input.setEnabled(curr_provider == "siliconflow")
        layout.addWidget(self.key_input)

        # 4. Model 名称 (支持下拉与手动自定义)
        layout.addWidget(QLabel("模型名称 (Model Name) *"))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.update_model_presets(curr_provider)

        curr_model = self.config.get("model", "deepseek-ai/DeepSeek-V4-Flash")
        self.model_combo.setEditText(curr_model)
        layout.addWidget(self.model_combo)

        # 5. 开启思考推理
        self.enable_thinking_cb = QCheckBox("启用深度思考与推理过程 (Think Mode)")
        self.enable_thinking_cb.setChecked(bool(self.config.get("enable_thinking", False)))
        layout.addWidget(self.enable_thinking_cb)

        # 6. 保存 / 取消按钮
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setText("保存配置")
        btn_box.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        btn_box.accepted.connect(self._validate_and_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _on_provider_changed(self, index: int):
        provider_key = self.provider_combo.currentData()
        if provider_key == "siliconflow":
            if not self.url_input.text() or "localhost" in self.url_input.text():
                self.url_input.setText("https://api.siliconflow.cn/v1")
            self.key_input.setEnabled(True)
        else:
            if not self.url_input.text() or "siliconflow" in self.url_input.text():
                self.url_input.setText("http://localhost:11434")
            self.key_input.setEnabled(False)
        self.update_model_presets(provider_key)

    def update_model_presets(self, provider: str):
        self.model_combo.clear()
        if provider == "siliconflow":
            presets = [
                "deepseek-ai/DeepSeek-V4-Flash",
                "deepseek-ai/DeepSeek-V3",
                "deepseek-ai/DeepSeek-R1",
                "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
                "Qwen/Qwen2.5-72B-Instruct",
                "THUDM/glm-4-9b-chat"
            ]
        else:
            presets = [
                "qwen2.5:7b",
                "qwen2.5:1.5b",
                "deepseek-r1:8b",
                "llama3:8b",
                "mistral:7b"
            ]
        self.model_combo.addItems(presets)

    def _validate_and_accept(self):
        if not self.model_combo.currentText().strip():
            QMessageBox.warning(self, "警告", "模型名称不能为空！")
            return
        self.accept()

    def get_config(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_combo.currentData(),
            "base_url": self.url_input.text().strip(),
            "siliconflow_api_key": self.key_input.text().strip(),
            "model": self.model_combo.currentText().strip(),
            "enable_thinking": self.enable_thinking_cb.isChecked()
        }


# =====================================================================
# 5. 系统托盘图标管理器 (SystemTrayIcon)
# =====================================================================

class TodoSystemTray(QSystemTrayIcon):
    """带动态绘制图标的系统托盘管理器"""

    def __init__(self, main_window: QMainWindow):
        super().__init__(main_window)
        self.main_window = main_window
        self.init_tray()

    def generate_tray_icon(self) -> QIcon:
        """使用 QPainter 动态绘制优雅的像素图标"""
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 背景底色
        painter.setBrush(QBrush(QColor("#3182CE")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(2, 2, 28, 28), 6, 6)

        # 打勾图标
        pen = QPen(QColor("#FFFFFF"), 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(8, 16, 14, 22)
        painter.drawLine(14, 22, 24, 10)
        painter.end()

        return QIcon(pixmap)

    def init_tray(self):
        self.setIcon(self.generate_tray_icon())
        self.setToolTip("Todo Agent 智能待办助手")

        tray_menu = QMenu()
        show_action = QAction("显示主窗口", self.main_window)
        show_action.triggered.connect(self.main_window.show_and_activate)
        tray_menu.addAction(show_action)

        add_action = QAction("+ 快速添加任务", self.main_window)
        add_action.triggered.connect(self.main_window.open_add_dialog)
        tray_menu.addAction(add_action)

        tray_menu.addSeparator()

        quit_action = QAction("退出系统", self.main_window)
        quit_action.triggered.connect(self.exit_application)
        tray_menu.addAction(quit_action)

        self.setContextMenu(tray_menu)
        self.activated.connect(self._on_activated)
        self.show()

    def exit_application(self):
        """退出系统并清理后台定时器与线程"""
        global_reminder_scheduler.stop_all()
        QApplication.quit()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.main_window.isVisible():
                self.main_window.hide()
            else:
                self.main_window.show_and_activate()


# =====================================================================
# 6. 主客户端窗口 (MainWindow)
# =====================================================================

class MainWindow(QMainWindow):
    """Todo Agent 客户端主窗口"""

    def __init__(self, db_path: str = "todos.db"):
        super().__init__()
        self.db_path = db_path
        self.config = load_config()
        self.current_filter = "all"
        self.init_ui()
        self.init_scheduler()
        self.refresh_todo_list()

    def closeEvent(self, event):
        """主窗口关闭时清理所有线程并彻底结束终端进程"""
        global_reminder_scheduler.stop_all()
        event.accept()
        QApplication.quit()

    def init_ui(self):
        self.setWindowTitle("Todo Agent - 智能待办桌面端")
        self.setMinimumSize(850, 650)

        # 核心主控 Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. 顶部 Header 栏
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 14, 20, 14)

        title_label = QLabel("📝 Todo Agent")
        title_label.setObjectName("appTitle")
        header_layout.addWidget(title_label)

        # 模型指示 Badge 按钮 (点击弹出 LLM 配置窗口)
        model_name = self.config.get("model", "DeepSeek-V4-Flash")
        self.model_badge = QPushButton(f"🧠 {model_name} ⚙️")
        self.model_badge.setObjectName("modelBadge")
        self.model_badge.setToolTip("点击配置大模型 Provider、Base URL 和 API Key")
        self.model_badge.setCursor(Qt.CursorShape.PointingHandCursor)
        self.model_badge.clicked.connect(self.open_model_config_dialog)
        header_layout.addWidget(self.model_badge)

        # 主题切换下拉框
        header_layout.addWidget(QLabel("主题:"))
        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("themeCombo")
        self.theme_combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.theme_combo.addItem("☀️ 浅色明亮", "light")
        self.theme_combo.addItem("🌙 赛博暗黑", "dark")
        self.theme_combo.addItem("❄️ 极光冰蓝", "nord")

        saved_theme = self.config.get("theme", "light")
        theme_map = {"light": 0, "dark": 1, "nord": 2}
        self.theme_combo.setCurrentIndex(theme_map.get(saved_theme, 0))
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        header_layout.addWidget(self.theme_combo)
        # 初始化启动时主动应用当前主题样式
        self.apply_theme(saved_theme)
        header_layout.addStretch()

        # 新建按钮
        self.btn_add = QPushButton("+ 新建任务")
        self.btn_add.setObjectName("btnPrimary")
        self.btn_add.clicked.connect(self.open_add_dialog)
        header_layout.addWidget(self.btn_add)

        main_layout.addWidget(header_frame)

        # 2. 中间区域（主列表）
        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(20, 16, 20, 16)
        list_layout.setSpacing(12)

        # 筛选工具栏
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("筛选:"))
        self.btn_filter_all = QPushButton("全部")
        self.btn_filter_pending = QPushButton("未完成")
        self.btn_filter_completed = QPushButton("已完成")

        for btn in [self.btn_filter_all, self.btn_filter_pending, self.btn_filter_completed]:
            btn.setCheckable(True)
            filter_layout.addWidget(btn)

        self.btn_filter_all.setChecked(True)
        self.btn_filter_all.clicked.connect(lambda: self.set_filter("all"))
        self.btn_filter_pending.clicked.connect(lambda: self.set_filter("pending"))
        self.btn_filter_completed.clicked.connect(lambda: self.set_filter("completed"))

        filter_layout.addStretch()

        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索待办事项...")
        self.search_input.setFixedWidth(220)
        self.search_input.textChanged.connect(self.refresh_todo_list)
        filter_layout.addWidget(self.search_input)

        list_layout.addLayout(filter_layout)

        # 任务列表组件
        self.todo_list_widget = QListWidget()
        list_layout.addWidget(self.todo_list_widget)

        main_layout.addWidget(list_container, stretch=1)

        # 3. 底部 AI 自然语言指令输入栏
        ai_input_frame = QFrame()
        ai_input_frame.setObjectName("aiInputFrame")
        ai_input_layout = QHBoxLayout(ai_input_frame)
        ai_input_layout.setContentsMargins(20, 10, 20, 10)
        ai_input_layout.setSpacing(10)

        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("✨ 输入 AI 智能体指令（例：'帮我安排明天上午10点和团队开会'）...")
        self.ai_input.returnPressed.connect(self.send_ai_command)
        ai_input_layout.addWidget(self.ai_input, stretch=1)

        self.btn_send_ai = QPushButton("🤖 AI 执行")
        self.btn_send_ai.setObjectName("btnPrimary")
        self.btn_send_ai.clicked.connect(self.send_ai_command)
        ai_input_layout.addWidget(self.btn_send_ai)

        main_layout.addWidget(ai_input_frame)

        # 4. 底部状态栏
        self.status_bar_widget = QStatusBar()
        self.setStatusBar(self.status_bar_widget)
        self.show_status("就绪 - Todo Agent SQLite 数据库已连接")

        # 5. 系统托盘
        self.tray = TodoSystemTray(self)

        # 6. 加载并应用已保存的主题
        self.apply_theme(saved_theme)

    def show_status(self, message: str):
        """统一安全地展示底部状态栏提示信息"""
        if hasattr(self, 'status_bar_widget') and self.status_bar_widget:
            self.status_bar_widget.showMessage(message)
        else:
            self.statusBar().showMessage(message)

    def show_and_activate(self):
        self.show()
        self.activateWindow()
        self.raise_()

    def set_filter(self, filter_type: str):
        self.current_filter = filter_type
        self.btn_filter_all.setChecked(filter_type == "all")
        self.btn_filter_pending.setChecked(filter_type == "pending")
        self.btn_filter_completed.setChecked(filter_type == "completed")
        self.refresh_todo_list()

    def open_model_config_dialog(self):
        dialog = ModelConfigDialog(self.config, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_cfg = dialog.get_config()
            self.config.update(new_cfg)
            save_config(self.config)
            model_name = self.config.get("model", "DeepSeek-V4-Flash")
            self.model_badge.setText(f"🧠 {model_name} ⚙️")
            provider = self.config.get("provider", "siliconflow")
            self.show_status(f"⚙️ LLM 配置已成功更新！[Provider: {provider}, Model: {model_name}]")

    def init_scheduler(self):
        """恢复待办任务中的定时提醒"""
        def _restore_db(db: TodoDatabase):
            return db.get_pending_reminders()

        def _on_restored(reminders):
            now = datetime.datetime.now()
            for t in reminders:
                try:
                    remind_dt = datetime.datetime.strptime(t["remind_at"], "%Y-%m-%d %H:%M:%S")
                    delay = (remind_dt - now).total_seconds()
                    if delay > 0:
                        global_reminder_scheduler.schedule_reminder(t["id"], t["title"], delay)
                except Exception:
                    pass

        self.run_worker(_restore_db, _on_restored)

    def run_worker(self, func, callback):
        """异步执行 SQLite 数据库任务"""
        worker = DbWorker(func, db_path=self.db_path)
        worker.finished_signal.connect(callback)
        worker.error_signal.connect(lambda err: self.show_status(f"❌ 错误: {err}"))
        worker.start()
        # 保持线程引用防止垃圾回收
        setattr(self, f"_worker_{id(worker)}", worker)

    def refresh_todo_list(self):
        """重新拉取数据库并更新待办列表 Card View"""
        search_kw = self.search_input.text().strip()

        def _query_db(db: TodoDatabase):
            sql = "SELECT * FROM todos WHERE 1=1"
            params = []

            if self.current_filter == "pending":
                sql += " AND completed = 0"
            elif self.current_filter == "completed":
                sql += " AND completed = 1"

            if search_kw:
                sql += " AND title LIKE ?"
                params.append(f"%{search_kw}%")

            sql += " ORDER BY completed ASC, priority DESC, id DESC"
            return db.query_sql(sql, tuple(params))

        def _on_loaded(todos: List[Dict[str, Any]]):
            self.todo_list_widget.clear()
            for t in todos:
                item = QListWidgetItem(self.todo_list_widget)
                widget = TodoItemWidget(t)
                widget.status_changed.connect(self._on_todo_status_changed)
                widget.delete_requested.connect(self._on_todo_delete)
                widget.edit_requested.connect(self.open_edit_dialog)

                item.setSizeHint(widget.sizeHint())
                self.todo_list_widget.addItem(item)
                self.todo_list_widget.setItemWidget(item, widget)

            self.show_status(f"当前共加载 {len(todos)} 项待办任务")

        def _fetch(db: TodoDatabase):
            return _query_db(db)

        self.run_worker(_fetch, _on_loaded)

    def open_add_dialog(self):
        dialog = AddEditTodoDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()

            def _add(db: TodoDatabase):
                return db.add_todo(
                    title=data["title"],
                    priority=data["priority"],
                    category=data["category"],
                    remind_at=data["remind_at"]
                )

            def _on_added(todo_id: int):
                if data["remind_at"]:
                    try:
                        remind_dt = datetime.datetime.strptime(data["remind_at"], "%Y-%m-%d %H:%M:%S")
                        delay = (remind_dt - datetime.datetime.now()).total_seconds()
                        if delay > 0:
                            global_reminder_scheduler.schedule_reminder(todo_id, data["title"], delay)
                    except Exception:
                        pass
                self.show_status(f"✅ 成功添加待办事项 [{data['title']}]")
                self.refresh_todo_list()

            self.run_worker(_add, _on_added)

    def open_edit_dialog(self, todo_data: Dict[str, Any]):
        dialog = AddEditTodoDialog(todo_data=todo_data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            todo_id = todo_data["id"]

            def _update(db: TodoDatabase):
                return db.update_todo(
                    todo_id=todo_id,
                    title=data["title"],
                    priority=data["priority"],
                    category=data["category"],
                    remind_at=data["remind_at"]
                )

            def _on_updated(success: bool):
                if success:
                    global_reminder_scheduler.cancel_reminder(todo_id)
                    if data["remind_at"]:
                        try:
                            remind_dt = datetime.datetime.strptime(data["remind_at"], "%Y-%m-%d %H:%M:%S")
                            delay = (remind_dt - datetime.datetime.now()).total_seconds()
                            if delay > 0:
                                global_reminder_scheduler.schedule_reminder(todo_id, data["title"], delay)
                        except Exception:
                            pass
                    self.show_status("✅ 待办事项更新成功")
                    self.refresh_todo_list()

            self.run_worker(_update, _on_updated)

    def _on_todo_status_changed(self, todo_id: int, is_completed: bool):
        def _update_status(db: TodoDatabase):
            if is_completed:
                return db.complete_todo(todo_id)
            else:
                return db.uncomplete_todo(todo_id)

        def _on_changed(success: bool):
            if is_completed:
                global_reminder_scheduler.cancel_reminder(todo_id)
            self.refresh_todo_list()

        self.run_worker(_update_status, _on_changed)

    def _on_todo_delete(self, todo_id: int):
        reply = QMessageBox.question(self, "确认删除", "确定要彻底删除该待办事项吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            def _delete(db: TodoDatabase):
                return db.delete_todo(todo_id)

            def _on_deleted(success: bool):
                if success:
                    global_reminder_scheduler.cancel_reminder(todo_id)
                    self.show_status("🗑️ 任务已成功删除")
                    self.refresh_todo_list()

            self.run_worker(_delete, _on_deleted)

    def _on_theme_changed(self, index: int):
        theme_key = self.theme_combo.currentData()
        self.apply_theme(theme_key)

    def apply_theme(self, theme_key: str):
        qss = THEMES.get(theme_key, LIGHT_QSS)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(qss)
        else:
            self.setStyleSheet(qss)
        self.config["theme"] = theme_key
        save_config(self.config)
        theme_name = self.theme_combo.currentText() if hasattr(self, 'theme_combo') and self.theme_combo else theme_key
        self.show_status(f"🎨 已成功切换至主题: {theme_name}")

    def _on_mode_changed(self, index: int):
        modes = ["agent", "prompts", "chat"]
        new_mode = modes[index]
        self.config["mode"] = new_mode
        save_config(self.config)
        self.show_status(f"💡 已切换工作模式为: {new_mode}")

    def send_ai_command(self):
        text = self.ai_input.text().strip()
        if not text:
            return

        self.ai_input.clear()
        self.btn_send_ai.setEnabled(False)
        self.show_status("🧠 AI 智能体分析思考并执行中...")

        worker = AIAgentWorker(text, self.config, db_path=self.db_path)

        def _on_ai_result(message: str, should_refresh: bool):
            self.btn_send_ai.setEnabled(True)
            # 在界面最底部状态栏展示成功提示
            self.show_status(f"✅ AI 任务执行完成：{message}")
            if should_refresh:
                self.refresh_todo_list()

        worker.result_signal.connect(_on_ai_result)
        worker.start()
        setattr(self, f"_ai_worker_{id(worker)}", worker)


# =====================================================================
# 7. 主程序入口函数
# =====================================================================

def main():
    # 允许终端 Ctrl+C (SIGINT) 直接退出程序
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)  # 用户关闭主窗口时自动退出应用程序

    # 定期唤醒 Python 解释器以支持捕获控制台 Ctrl+C 信号
    sig_timer = QTimer()
    sig_timer.start(500)
    sig_timer.timeout.connect(lambda: None)

    window = MainWindow()
    window.show()

    ret = app.exec()
    global_reminder_scheduler.stop_all()
    sys.exit(ret)


if __name__ == "__main__":
    main()
