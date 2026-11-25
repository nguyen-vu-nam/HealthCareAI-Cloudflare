from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, profile_view, dashboard_view, chat_view, WaterLogViewSet, SleepLogViewSet, ActivityLogViewSet, ReminderViewSet, register_push_device, unregister_push_device, test_push_notification, daily_goal_view, chat_history_view

router = DefaultRouter()
router.register("water-logs", WaterLogViewSet, basename="water-log")
router.register("sleep-logs", SleepLogViewSet, basename="sleep-log")
router.register("activity-logs", ActivityLogViewSet, basename="activity-log")
router.register("reminders", ReminderViewSet, basename="reminder")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("profile/", profile_view, name="profile"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("daily-goal/", daily_goal_view, name="daily-goal"),
    path("chat/", chat_view, name="chat"),
    path("chat/history/", chat_history_view, name="chat-history"),
    path("push/register/", register_push_device, name="push-register"),
    path("push/unregister/", unregister_push_device, name="push-unregister"),
    path("push/test/", test_push_notification, name="push-test"),
    path("", include(router.urls)),
]
