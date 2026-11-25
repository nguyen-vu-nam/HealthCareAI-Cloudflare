from django.contrib import admin
from .models import HealthProfile, WaterLog, SleepLog, ActivityLog, Reminder, PushDevice

admin.site.register(HealthProfile)
admin.site.register(WaterLog)
admin.site.register(SleepLog)
admin.site.register(ActivityLog)
admin.site.register(Reminder)
admin.site.register(PushDevice)
