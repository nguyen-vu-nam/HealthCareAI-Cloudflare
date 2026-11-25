import time
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum
from health.models import Reminder, DailyGoal, WaterLog, SleepLog, ActivityLog
from health.push import send_to_user

class Command(BaseCommand):
    help = "Kiểm tra nhắc nhở theo giờ Việt Nam và gửi qua Firebase Cloud Messaging"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("HealthCare AI reminder worker đang chạy (Asia/Ho_Chi_Minh)..."))
        while True:
            now = timezone.localtime(timezone.now())
            # Lấy reminder nằm trong phút hiện tại; tránh phụ thuộc giây khởi động worker.
            due = Reminder.objects.filter(
                enabled=True,
                reminder_time__hour=now.hour,
                reminder_time__minute=now.minute,
            ).exclude(last_sent_on=now.date()).select_related("user")
            for reminder in due:
                try:
                    result = send_to_user(reminder.user, "HealthCare AI · Nhắc nhở", reminder.title)
                    if result["sent"]:
                        reminder.last_sent_on = now.date()
                        if not reminder.repeat_daily:
                            reminder.enabled = False
                        reminder.save(update_fields=["last_sent_on", "enabled"])
                        self.stdout.write(self.style.SUCCESS(
                            f"[{now:%d/%m/%Y %H:%M:%S}] Đã gửi nhắc nhở #{reminder.id} tới {result['sent']} thiết bị."
                        ))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"[{now:%H:%M:%S}] Nhắc nhở #{reminder.id} chưa gửi: {result['message']}"
                        ))
                except Exception as exc:
                    self.stderr.write(self.style.ERROR(f"Nhắc nhở #{reminder.id}: {exc}"))
            # Nhắc mục tiêu sức khỏe cuối ngày, mỗi tài khoản tối đa một lần/ngày.
            goals = DailyGoal.objects.filter(alert_time__hour=now.hour, alert_time__minute=now.minute).select_related("user")
            for goal in goals:
                if goal.last_alert_on == now.date():
                    continue
                water_done = WaterLog.objects.filter(user=goal.user, recorded_at__date=now.date()).aggregate(v=Sum("amount_ml"))["v"] or 0
                sleep_done = SleepLog.objects.filter(user=goal.user, sleep_date=now.date()).aggregate(v=Sum("sleep_hours"))["v"] or 0
                activity_done = ActivityLog.objects.filter(user=goal.user, activity_date=now.date()).aggregate(v=Sum("duration_minutes"))["v"] or 0
                missing = []
                if water_done < goal.water_target_ml: missing.append(f"nước {water_done}/{goal.water_target_ml} ml")
                if sleep_done < goal.sleep_target_hours: missing.append(f"ngủ {sleep_done:g}/{goal.sleep_target_hours:g} giờ")
                if activity_done < goal.activity_target_minutes: missing.append(f"vận động {activity_done}/{goal.activity_target_minutes} phút")
                if missing:
                    result = send_to_user(goal.user, "HealthCare AI · Tổng kết hôm nay", "Bạn còn thiếu mục tiêu: " + ", ".join(missing) + ". Hãy xem lại kế hoạch sức khỏe nhé!")
                    if result["sent"]:
                        goal.last_alert_on = now.date()
                        goal.save(update_fields=["last_alert_on", "updated_at"])
            time.sleep(10)
