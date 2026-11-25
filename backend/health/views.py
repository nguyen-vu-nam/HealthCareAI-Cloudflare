from datetime import date, datetime, timedelta
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Sum, Avg
from django.utils import timezone
from rest_framework import generics, viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
import requests
import logging

logger = logging.getLogger(__name__)
from .models import HealthProfile, WaterLog, SleepLog, ActivityLog, Reminder, PushDevice, DailyGoal, ChatConversation, ChatMessage
from .serializers import (
    RegisterSerializer, ProfileSerializer, WaterLogSerializer,
    SleepLogSerializer, ActivityLogSerializer, ReminderSerializer
)

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class OwnedModelViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class WaterLogViewSet(OwnedModelViewSet):
    queryset = WaterLog.objects.all()
    serializer_class = WaterLogSerializer

class SleepLogViewSet(OwnedModelViewSet):
    queryset = SleepLog.objects.all()
    serializer_class = SleepLogSerializer

class ActivityLogViewSet(OwnedModelViewSet):
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer

class ReminderViewSet(OwnedModelViewSet):
    queryset = Reminder.objects.all()
    serializer_class = ReminderSerializer

@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def profile_view(request):
    profile, _ = HealthProfile.objects.get_or_create(user=request.user)
    if request.method == "PATCH":
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
    else:
        serializer = ProfileSerializer(profile)
    return Response(serializer.data)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_view(request):
    today = timezone.localdate()
    try:
        start = date.fromisoformat(request.query_params.get("start_date", (today - timedelta(days=6)).isoformat()))
        end = date.fromisoformat(request.query_params.get("end_date", today.isoformat()))
        if start > end:
            return Response({"detail": "Ngày bắt đầu phải nhỏ hơn hoặc bằng ngày kết thúc."}, status=400)
    except ValueError:
        return Response({"detail": "Định dạng ngày không hợp lệ. Dùng YYYY-MM-DD."}, status=400)

    profile, _ = HealthProfile.objects.get_or_create(user=request.user)
    bmi = None
    bmi_label = None
    if profile.weight_kg and profile.height_cm and profile.height_cm > 0:
        bmi = round(profile.weight_kg / ((profile.height_cm / 100) ** 2), 2)
        bmi_label = "Thiếu cân" if bmi < 18.5 else "Khoảng bình thường" if bmi < 25 else "Thừa cân" if bmi < 30 else "Béo phì"
    water_target = round(profile.weight_kg * 35) if profile.weight_kg else None

    water_qs = WaterLog.objects.filter(user=request.user, recorded_at__date__gte=start, recorded_at__date__lte=end)
    sleep_qs = SleepLog.objects.filter(user=request.user, sleep_date__gte=start, sleep_date__lte=end)
    activity_qs = ActivityLog.objects.filter(user=request.user, activity_date__gte=start, activity_date__lte=end)

    daily = []
    cursor = start
    while cursor <= end:
        water_total = water_qs.filter(recorded_at__date=cursor).aggregate(total=Sum("amount_ml"))["total"] or 0
        sleep_value = sleep_qs.filter(sleep_date=cursor).aggregate(avg=Avg("sleep_hours"))["avg"]
        activity_total = activity_qs.filter(activity_date=cursor).aggregate(total=Sum("duration_minutes"))["total"] or 0
        daily.append({
            "date": cursor.isoformat(),
            "total_water_ml": water_total,
            "sleep_hours": round(sleep_value, 1) if sleep_value is not None else None,
            "activity_minutes": activity_total,
        })
        cursor += timedelta(days=1)

    return Response({
        "bmi": bmi, "bmi_label": bmi_label, "water_target_ml": water_target,
        "period": {"start_date": start.isoformat(), "end_date": end.isoformat()},
        "daily_data": daily,
    })

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def chat_history_view(request):
    """Lấy lịch sử chat hoặc nhập lịch sử cũ từ trình duyệt vào database."""
    conversation = ChatConversation.objects.filter(user=request.user).first()

    if request.method == "POST":
        if conversation and conversation.messages.exists():
            return Response({"detail": "Lịch sử chat trong database đã tồn tại."}, status=409)
        incoming = request.data.get("messages", [])
        if not isinstance(incoming, list) or len(incoming) > 500:
            return Response({"detail": "Danh sách tin nhắn không hợp lệ (tối đa 500)."}, status=400)

        valid_messages = []
        for item in incoming:
            if isinstance(item, dict):
                role, content = item.get("role"), item.get("text")
                if role in ("user", "ai") and isinstance(content, str) and content.strip():
                    valid_messages.append(ChatMessage(role=role, content=content[:20000]))

        if valid_messages:
            title = next((m.content[:200] for m in valid_messages if m.role == "user"), "Cuộc trò chuyện sức khỏe")
            conversation, _ = ChatConversation.objects.get_or_create(
                user=request.user, defaults={"title": title}
            )
            for item in valid_messages:
                item.conversation = conversation
            ChatMessage.objects.bulk_create(valid_messages)
            conversation.save()

    if not conversation:
        return Response({"conversation_id": None, "messages": []})

    return Response({
        "conversation_id": conversation.id,
        "messages": [
            {"id": item.id, "role": item.role, "text": item.content, "created_at": item.created_at}
            for item in conversation.messages.all()
        ],
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat_view(request):
    question = (request.data.get("message") or "").strip()
    if not question:
        return Response({"detail": "Vui lòng nhập câu hỏi."}, status=400)
    if len(question) > 4000:
        return Response({"detail": "Câu hỏi quá dài (tối đa 4000 ký tự)."}, status=400)

    # Mỗi tài khoản có một cuộc trò chuyện được lưu lâu dài trong database.
    conversation, _ = ChatConversation.objects.get_or_create(
        user=request.user,
        defaults={"title": question[:200]}
    )
    ChatMessage.objects.create(
        conversation=conversation,
        role="user",
        content=question
    )

    api_base = settings.AI_API_BASE_URL.strip()
    api_key = settings.AI_API_KEY.strip()
    model = settings.AI_MODEL.strip()
    if not api_base or not api_key:
        reply = "Chatbot chưa được cấu hình API. Quản trị viên cần thiết lập AI_API_BASE_URL, AI_API_KEY và AI_MODEL trong môi trường triển khai."
        ChatMessage.objects.create(conversation=conversation, role="ai", content=reply)
        conversation.save()
        return Response({
            "reply": reply,
            "configured": False,
            "conversation_id": conversation.id,
        })

    profile, _ = HealthProfile.objects.get_or_create(user=request.user)
    today = timezone.localdate()
    recent = today - timedelta(days=6)

    age = None
    if profile.birth_date:
        age = today.year - profile.birth_date.year - (
            (today.month, today.day) < (profile.birth_date.month, profile.birth_date.day)
        )

    bmi = None
    bmi_category = None
    if profile.weight_kg and profile.height_cm and profile.height_cm > 0:
        bmi = round(profile.weight_kg / ((profile.height_cm / 100) ** 2), 1)
        bmi_category = (
            "Thiếu cân" if bmi < 18.5 else
            "Bình thường" if bmi < 25 else
            "Thừa cân" if bmi < 30 else "Béo phì"
        )

    water_by_day = []
    for day_offset in range(7):
        day = recent + timedelta(days=day_offset)
        total = WaterLog.objects.filter(
            user=request.user, recorded_at__date=day
        ).aggregate(total=Sum("amount_ml"))["total"] or 0
        water_by_day.append(total)
    days_with_water_logs = sum(1 for amount in water_by_day if amount > 0)
    avg_daily_water = (
        round(sum(water_by_day) / days_with_water_logs)
        if days_with_water_logs else None
    )

    avg_sleep = SleepLog.objects.filter(
        user=request.user, sleep_date__gte=recent, sleep_date__lte=today
    ).aggregate(v=Avg("sleep_hours"))["v"]
    avg_activity = ActivityLog.objects.filter(
        user=request.user, activity_date__gte=recent, activity_date__lte=today
    ).aggregate(v=Avg("duration_minutes"))["v"]

    goal, _ = DailyGoal.objects.get_or_create(user=request.user)

    context = {
        "profile": {
            "full_name": profile.full_name or None,
            "age_years": age,
            "gender": profile.gender or None,
            "height_cm": profile.height_cm,
            "weight_kg": profile.weight_kg,
            "bmi": bmi,
            "bmi_category": bmi_category,
        },
        "daily_goals": {
            "water_ml": goal.water_ml,
            "sleep_hours": goal.sleep_hours,
            "activity_minutes": goal.activity_minutes,
        },
        "last_7_days": {
            "average_daily_water_ml_on_days_with_logs": avg_daily_water,
            "average_sleep_hours": round(avg_sleep, 1) if avg_sleep is not None else None,
            "average_activity_minutes_per_log": round(avg_activity, 1) if avg_activity is not None else None,
            "days_with_water_logs": days_with_water_logs,
        },
        "data_notes": [
            "Giá trị null nghĩa là người dùng chưa cung cấp hoặc chưa có dữ liệu ghi nhận.",
            "Không được tự suy đoán hoặc tự điền các giá trị còn thiếu.",
            "Số liệu theo dõi chỉ phản ánh dữ liệu đã ghi trong ứng dụng."
        ],
    }
    system_prompt = (
        "Bạn là trợ lý sức khỏe HealthCare AI, giao tiếp bằng tiếng Việt tự nhiên, thân thiện. "
        "QUY TẮC TRẢ LỜI BẮT BUỘC:\n"
        "1. Ưu tiên câu trả lời ngắn gọn, trực tiếp, dễ hiểu.\n"
        "2. Câu hỏi thông thường: khoảng 3-5 câu.\n"
        "3. Câu hỏi cần hướng dẫn: tối đa 5 ý chính.\n"
        "4. Không tự ý viết bài dài, không lặp lại nội dung, không đưa bảng nếu không cần thiết.\n"
        "5. Chỉ phân tích chuyên sâu, lập kế hoạch chi tiết khi người dùng yêu cầu.\n"
        "6. Nếu câu hỏi đơn giản, trả lời thẳng vào trọng tâm.\n"
        "7. Luôn ưu tiên thông tin quan trọng và lời khuyên có thể áp dụng ngay.\n"
        "8. Không chẩn đoán bệnh, không kê đơn, không thay thế bác sĩ.\n"
        "9. Khi có dấu hiệu nguy hiểm, phải khuyến nghị người dùng đến cơ sở y tế.\n"
        "10. Không tự bịa dữ liệu cá nhân hoặc suy diễn thông tin chưa được cung cấp.\n"
        "11. Hãy đối chiếu câu hỏi với hồ sơ sức khỏe và mục tiêu cá nhân bên dưới.\\n"
        "12. Chỉ nhắc dữ liệu cá nhân khi liên quan; không đọc lại toàn bộ hồ sơ trong mọi câu trả lời.\\n"
        "13. Nếu thiếu dữ liệu quan trọng để tư vấn an toàn, hãy hỏi người dùng thay vì đoán.\\n"
        "14. Nếu dữ liệu bất thường hoặc có vẻ không hợp lý, hãy xác nhận lại trước khi sử dụng.\\n"
        f"HỒ SƠ SỨC KHỎE VÀ DỮ LIỆU THEO DÕI CỦA TÀI KHOẢN ĐANG ĐĂNG NHẬP: {context}"
    )
    url = api_base.rstrip("/")
    if not url.endswith("/chat/completions"):
        url += "/chat/completions"
    try:
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                "temperature": 0.5,
                "max_tokens": 600,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not reply:
            raise ValueError("AI response empty")
        ChatMessage.objects.create(
            conversation=conversation,
            role="ai",
            content=reply
        )
        conversation.save()
        return Response({
            "reply": reply,
            "configured": True,
            "conversation_id": conversation.id,
        })
    except (requests.RequestException, ValueError, KeyError, IndexError) as exc:
        logger.exception("Xkiro chat request failed: %s", exc)
        error_reply = "Chatbot hiện chưa phản hồi, vui lòng thử lại sau."
        ChatMessage.objects.create(
            conversation=conversation,
            role="ai",
            content=error_reply
        )
        conversation.save()
        return Response({
            "reply": error_reply,
            "configured": False,
            "conversation_id": conversation.id,
        }, status=502)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_push_device(request):
    token = (request.data.get("token") or "").strip()
    user_agent = (request.data.get("user_agent") or "")[:500]
    if not token:
        return Response({"detail": "Thiếu FCM token."}, status=400)
    # A token belongs to the most recently authenticated account on this browser.
    PushDevice.objects.filter(token=token).exclude(user=request.user).delete()
    device, _ = PushDevice.objects.update_or_create(
        token=token, defaults={"user": request.user, "user_agent": user_agent, "active": True}
    )
    return Response({"registered": True, "device_id": device.id})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def unregister_push_device(request):
    token = (request.data.get("token") or "").strip()
    if token:
        PushDevice.objects.filter(user=request.user, token=token).update(active=False)
    return Response({"registered": False})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def test_push_notification(request):
    from .push import send_to_user
    result = send_to_user(
        request.user,
        "HealthCare AI",
        "Thông báo thử nghiệm đã được gửi thành công!"
    )
    if result["sent"] == 0:
        return Response({"detail": result["message"]}, status=400)
    return Response({"sent": result["sent"], "failed": result["failed"]})


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def daily_goal_view(request):
    goal, _ = DailyGoal.objects.get_or_create(user=request.user)

    if request.method == "PATCH":
        allowed_fields = {
            "water_ml": int,
            "sleep_hours": float,
            "activity_minutes": int,
        }
        errors = {}
        updates = {}

        for field, field_type in allowed_fields.items():
            if field not in request.data:
                continue
            try:
                value = field_type(request.data[field])
                if value <= 0:
                    errors[field] = "Giá trị phải lớn hơn 0."
                elif field == "water_ml" and value > 10000:
                    errors[field] = "Mục tiêu nước không được vượt quá 10000 ml."
                elif field == "sleep_hours" and value > 24:
                    errors[field] = "Số giờ ngủ không được vượt quá 24."
                elif field == "activity_minutes" and value > 1440:
                    errors[field] = "Thời gian vận động không hợp lệ."
                else:
                    updates[field] = value
            except (ValueError, TypeError):
                errors[field] = "Giá trị không hợp lệ."

        if "alert_time" in request.data:
            try:
                alert_time = str(request.data["alert_time"])
                datetime.strptime(alert_time, "%H:%M")
                updates["alert_time"] = alert_time
            except (ValueError, TypeError):
                errors["alert_time"] = "Giờ nhắc nhở không hợp lệ."

        if errors:
            return Response({"errors": errors}, status=400)

        for field, value in updates.items():
            setattr(goal, field, value)
        if updates:
            goal.save()

    return Response({
        "water_ml": goal.water_ml,
        "sleep_hours": goal.sleep_hours,
        "activity_minutes": goal.activity_minutes,
        "alert_time": goal.alert_time.strftime("%H:%M"),
        "updated_at": goal.updated_at,
    })
