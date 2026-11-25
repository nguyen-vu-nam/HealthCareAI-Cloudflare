from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import HealthProfile, WaterLog, SleepLog, ActivityLog, Reminder, DailyGoal

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    class Meta:
        model = User
        fields = ("username", "email", "password", "full_name")
    def create(self, validated_data):
        full_name = validated_data.pop("full_name", "")
        user = User.objects.create_user(**validated_data)
        HealthProfile.objects.create(user=user, full_name=full_name)
        return user

class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    class Meta:
        model = HealthProfile
        fields = ("id", "username", "email", "full_name", "birth_date", "gender", "height_cm", "weight_kg", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

class WaterLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterLog
        fields = ("id", "amount_ml", "recorded_at", "note", "created_at")
        read_only_fields = ("id", "created_at")

class SleepLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SleepLog
        fields = ("id", "sleep_hours", "sleep_date", "note", "created_at")
        read_only_fields = ("id", "created_at")

class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = ("id", "activity_type", "duration_minutes", "activity_date", "note", "created_at")
        read_only_fields = ("id", "created_at")

class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = ("id", "title", "reminder_type", "reminder_time", "repeat_daily", "enabled", "created_at")
        read_only_fields = ("id", "created_at")


class DailyGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyGoal
        fields = ("water_target_ml", "sleep_target_hours", "activity_target_minutes", "alert_time")
