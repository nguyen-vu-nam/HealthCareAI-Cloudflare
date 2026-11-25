# Generated for HealthCare AI FCM integration.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="ActivityLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("activity_type", models.CharField(choices=[("walking","Đi bộ"),("running","Chạy bộ"),("cycling","Đạp xe"),("gym","Tập gym"),("yoga","Yoga"),("swimming","Bơi lội"),("other","Khác")], default="walking", max_length=20)),
                ("duration_minutes", models.PositiveIntegerField()),
                ("activity_date", models.DateField()),
                ("note", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activity_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering":["-activity_date"]},
        ),
        migrations.CreateModel(
            name="HealthProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(blank=True, max_length=150)),
                ("birth_date", models.DateField(blank=True, null=True)),
                ("gender", models.CharField(blank=True, max_length=20)),
                ("height_cm", models.FloatField(blank=True, null=True)),
                ("weight_kg", models.FloatField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="health_profile", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Reminder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=150)),
                ("reminder_type", models.CharField(default="general", max_length=30)),
                ("reminder_time", models.TimeField()),
                ("repeat_daily", models.BooleanField(default=True)),
                ("enabled", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reminders", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering":["reminder_time"]},
        ),
        migrations.CreateModel(
            name="SleepLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sleep_hours", models.FloatField()),
                ("sleep_date", models.DateField()),
                ("note", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sleep_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering":["-sleep_date"]},
        ),
        migrations.CreateModel(
            name="WaterLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount_ml", models.PositiveIntegerField()),
                ("recorded_at", models.DateTimeField()),
                ("note", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="water_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering":["-recorded_at"]},
        ),
    ]
