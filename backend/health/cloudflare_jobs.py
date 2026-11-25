from django.utils import timezone
from django.db.models import Sum
from .models import Reminder, DailyGoal, WaterLog, SleepLog, ActivityLog
from .push import send_to_user

def process_due_jobs():
    now = timezone.localtime(timezone.now())
    today = now.date()
    sent_reminders = 0
    due = Reminder.objects.filter(
        enabled=True,
        reminder_time__hour=now.hour,
        reminder_time__minute=now.minute,
    ).exclude(last_sent_on=today).select_related("user")

    for reminder in due:
        try:
            result = send_to_user(reminder.user, "HealthCare AI · Nhắc nhở", reminder.title)
            if result.get("sent", 0):
                reminder.last_sent_on = today
                if not reminder.repeat_daily:
                    reminder.enabled = False
                reminder.save(update_fields=["last_sent_on", "enabled"])
                sent_reminders += 1
        except Exception as exc:
            print(f"Reminder #{reminder.pk} failed: {exc}")

    goals = DailyGoal.objects.filter(
        alert_time__hour=now.hour, alert_time__minute=now.minute
    ).select_related("user")
    for goal in goals:
        if goal.last_alert_on == today:
            continue
        water_done = WaterLog.objects.filter(user=goal.user, recorded_at__date=today).aggregate(v=Sum("amount_ml"))["v"] or 0
        sleep_done = SleepLog.objects.filter(user=goal.user, sleep_date=today).aggregate(v=Sum("sleep_hours"))["v"] or 0
        activity_done = ActivityLog.objects.filter(user=goal.user, activity_date=today).aggregate(v=Sum("duration_minutes"))["v"] or 0
        missing = []
        if water_done < goal.water_ml: missing.append(f"nước {water_done}/{goal.water_ml} ml")
        if sleep_done < goal.sleep_hours: missing.append(f"ngủ {sleep_done:g}/{goal.sleep_hours:g} giờ")
        if activity_done < goal.activity_minutes: missing.append(f"vận động {activity_done}/{goal.activity_minutes} phút")
        if missing:
            try:
                result = send_to_user(goal.user, "HealthCare AI · Tổng kết hôm nay", "Bạn còn thiếu mục tiêu: " + ", ".join(missing) + ". Hãy xem lại kế hoạch sức khỏe nhé!")
                if result.get("sent", 0):
                    goal.last_alert_on = today
                    goal.save(update_fields=["last_alert_on", "updated_at"])
            except Exception as exc:
                print(f"DailyGoal for user #{goal.user_id} failed: {exc}")
    print(f"Cron completed at {now.isoformat()}; reminders sent={sent_reminders}")
