import threading
import winsound
import subprocess
import datetime
from typing import Dict, Any, Optional


def show_desktop_notification(title: str, message: str, enable_sound: bool = True) -> None:
    """播放提示音并在 Windows 桌面右下角显示弹窗提醒"""
    if enable_sound:
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass

    ps_script = f"""
    [void] [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms')
    $notify = New-Object System.Windows.Forms.NotifyIcon
    $notify.Icon = [System.Drawing.SystemIcons]::Information
    $notify.Visible = $true
    $notify.ShowBalloonTip(10000, '{title}', '{message}', [System.Windows.Forms.ToolTipIcon]::Info)
    """
    try:
        subprocess.Popen(["powershell", "-NoProfile", "-Command", ps_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


class ReminderScheduler:
    """后台定时提醒调度管理器"""

    def __init__(self):
        self.timers: Dict[int, threading.Timer] = {}

    def schedule_reminder(self, todo_id: int, title: str, delay_seconds: float, enable_sound: bool = True) -> None:
        """调度一个定时提醒任务"""
        if delay_seconds <= 0:
            return

        def _on_trigger():
            print(f"\n\n⏰ 【任务提醒】待办事项 [{todo_id}]: {title}\n用户: ", end="", flush=True)
            show_desktop_notification(
                title=f"⏰ Todo Agent 任务提醒 [{todo_id}]",
                message=f"任务：{title}",
                enable_sound=enable_sound
            )
            if todo_id in self.timers:
                del self.timers[todo_id]

        self.cancel_reminder(todo_id)
        timer = threading.Timer(delay_seconds, _on_trigger)
        timer.daemon = True
        self.timers[todo_id] = timer
        timer.start()

    def cancel_reminder(self, todo_id: int) -> None:
        """取消已有的定时提醒任务"""
        if todo_id in self.timers:
            try:
                self.timers[todo_id].cancel()
            except Exception:
                pass
            del self.timers[todo_id]

    def stop_all(self) -> None:
        """停止并清理所有后台定时提醒线程"""
        for timer in list(self.timers.values()):
            try:
                timer.cancel()
            except Exception:
                pass
        self.timers.clear()


global_reminder_scheduler = ReminderScheduler()

