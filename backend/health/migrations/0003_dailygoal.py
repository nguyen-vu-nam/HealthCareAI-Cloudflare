from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("health", "0002_fcm_push_devices"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name="DailyGoal", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("water_target_ml", models.PositiveIntegerField(default=2000)), ("sleep_target_hours", models.FloatField(default=8)), ("activity_target_minutes", models.PositiveIntegerField(default=30)), ("alert_time", models.TimeField(default="21:00")), ("last_alert_on", models.DateField(blank=True, null=True)), ("updated_at", models.DateTimeField(auto_now=True)), ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="daily_goal", to=settings.AUTH_USER_MODEL))]) ]
