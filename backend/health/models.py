from django.conf import settings
from django.db import models

class HealthProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="health_profile")
    full_name = models.CharField(max_length=150, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    height_cm = models.FloatField(null=True, blank=True)
    weight_kg = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name or self.user.username

class WaterLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="water_logs")
    amount_ml = models.PositiveIntegerField()
    recorded_at = models.DateTimeField()
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-recorded_at"]

class SleepLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sleep_logs")
    sleep_hours = models.FloatField()
    sleep_date = models.DateField()
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-sleep_date"]

class ActivityLog(models.Model):
    ACTIVITY_TYPES = [
        ("walking", "Đi bộ"), ("running", "Chạy bộ"), ("cycling", "Đạp xe"),
        ("gym", "Tập gym"), ("yoga", "Yoga"), ("swimming", "Bơi lội"), ("other", "Khác"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activity_logs")
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, default="walking")
    duration_minutes = models.PositiveIntegerField()
    activity_date = models.DateField()
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-activity_date"]

class Reminder(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reminders")
    title = models.CharField(max_length=150)
    reminder_type = models.CharField(max_length=30, default="general")
    reminder_time = models.TimeField()
    repeat_daily = models.BooleanField(default=True)
    enabled = models.BooleanField(default=True)
    last_sent_on = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["reminder_time"]


class PushDevice(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="push_devices")
    token = models.TextField(unique=True)
    user_agent = models.CharField(max_length=500, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.token[:18]}"


class DailyGoal(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_goal"
    )
    water_ml = models.PositiveIntegerField(default=2000)
    sleep_hours = models.FloatField(default=8)
    activity_minutes = models.PositiveIntegerField(default=30)

    alert_time = models.TimeField(default="21:00")
    last_alert_on = models.DateField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Daily goals - {self.user.username}"

class ChatConversation(models.Model):
    """Một cuộc trò chuyện chính cho mỗi tài khoản người dùng."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_conversation"
    )
    title = models.CharField(max_length=200, default="Cuộc trò chuyện sức khỏe")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Chat - {self.user.username}"


class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ("user", "Người dùng"),
        ("ai", "Trợ lý AI"),
    ]
    conversation = models.ForeignKey(
        ChatConversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.role}: {self.content[:60]}"
