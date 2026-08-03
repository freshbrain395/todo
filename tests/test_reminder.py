import pytest
import time
from reminder_scheduler import ReminderScheduler


def test_schedule_and_cancel_reminder():
    scheduler = ReminderScheduler()
    scheduler.schedule_reminder(todo_id=999, title="测试喝水提醒", delay_seconds=100)
    assert 999 in scheduler.timers

    scheduler.cancel_reminder(999)
    assert 999 not in scheduler.timers


def test_reminder_trigger_format(capsys):
    scheduler = ReminderScheduler()
    scheduler.schedule_reminder(todo_id=888, title="测试提醒格式", delay_seconds=0.1, enable_sound=False)
    time.sleep(0.3)

    captured = capsys.readouterr()
    assert "⏰ 【任务提醒】待办事项 [888]: 测试提醒格式" in captured.out
