import os
from django.conf import settings
from .models import PushDevice

_firebase_app = None

def _is_cloudflare():
    try:
        from workers import env  # noqa: F401
        return True
    except Exception:
        return False

def get_firebase_app():
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app
    if _is_cloudflare():
        raise RuntimeError("Firebase Admin SDK chưa được xác nhận tương thích với Python Workers. Cần tích hợp FCM HTTP v1 trước khi bật Push trên Cloudflare.")
    from pathlib import Path
    credential_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_FILE", "firebase-service-account.json").strip()
    path = Path(credential_path)
    if not path.is_absolute():
        path = settings.BASE_DIR / path
    if not path.is_file():
        raise RuntimeError(f"Không tìm thấy Firebase Service Account: {path}. Hãy đặt file JSON mới vào backend.")
    import firebase_admin
    from firebase_admin import credentials
    _firebase_app = firebase_admin.initialize_app(credentials.Certificate(str(path)))
    return _firebase_app

def send_to_user(user, title, body):
    devices = list(PushDevice.objects.filter(user=user, active=True))
    if not devices:
        return {"sent": 0, "failed": 0, "message": "Tài khoản chưa đăng ký thiết bị nhận thông báo."}
    # Firebase Admin SDK is not included in the Workers dependency set and has not
    # been validated on Pyodide. Fail closed with a clear status instead of import error.
    if _is_cloudflare():
        return {
            "sent": 0,
            "failed": len(devices),
            "message": "Firebase Push chưa được tích hợp FCM HTTP v1 cho Cloudflare Workers.",
        }
    from firebase_admin import messaging
    app = get_firebase_app()
    sent = failed = 0
    errors = []
    for device in devices:
        try:
            message = messaging.Message(
                data={"title": str(title), "body": str(body), "url": "/"},
                token=device.token,
                webpush=messaging.WebpushConfig(
                    headers={"Urgency": "high", "TTL": "86400"},
                    data={"title": str(title), "body": str(body), "url": "/"},
                ),
            )
            messaging.send(message, app=app)
            sent += 1
        except messaging.UnregisteredError:
            device.active = False
            device.save(update_fields=["active"])
            failed += 1
            errors.append("Có thiết bị đã hủy đăng ký nhận thông báo.")
        except Exception as exc:
            failed += 1
            errors.append(str(exc))
    return {"sent": sent, "failed": failed, "message": "; ".join(errors) if errors else "Gửi FCM thành công."}
