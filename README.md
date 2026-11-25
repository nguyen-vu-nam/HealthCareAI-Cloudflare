# HealthCare AI – Nhóm 12

## Chạy toàn bộ bằng một lần bấm

1. Cài **Python 3.11** và **Node.js LTS**.
2. Giải nén toàn bộ thư mục dự án.
3. Nhấp đúp `CHAY_HEALTHCARE_AI.bat`.
4. Lần đầu chạy, BAT tự tạo môi trường Python, cài thư viện, tạo `.env` mẫu nếu chưa có, chạy migration và mở 3 cửa sổ tiến trình (Backend, Reminder Worker, Frontend).
5. Truy cập `http://localhost:5173`.

Để thiết bị khác cùng Wi-Fi truy cập:
- Chạy `ipconfig` trên máy chủ, tìm IPv4, ví dụ `192.168.1.20`.
- Trên thiết bị kia mở `http://192.168.1.20:5173`.
- Nếu không vào được, cho phép Python và Node.js qua Windows Firewall trên mạng Private.

## Cấu hình thông báo Firebase

- Đặt **Service Account JSON mới** tại `backend/firebase-service-account.json`.
- `backend/.env` được tạo từ `.env.example`; kiểm tra `FIREBASE_SERVICE_ACCOUNT_FILE=firebase-service-account.json`.
- `frontend/.env` được tạo từ `.env.example`; Firebase Web config và VAPID public key đã điền.
- Đăng nhập trên từng thiết bị, vào Nhắc nhở, bật thông báo và cấp quyền trình duyệt; sau đó bấm Gửi thông báo thử.
- Worker phải chạy liên tục để gửi nhắc nhở đúng giờ. BAT tự mở worker.

**Bảo mật:** ZIP không chứa Firebase Service Account private key. Key từng được chia sẻ trước đó cần thu hồi trong Firebase Console và tạo key mới. Không gửi key mới lên chat hoặc đưa lên Git.

## Giới hạn Web Push trên LAN

Trang web có thể truy cập bằng HTTP trong mạng LAN. Tuy nhiên Web Push/Service Worker trên thiết bị khác thường yêu cầu **HTTPS** (ngoại lệ `localhost`). Vì vậy muốn nhận thông báo nền trên điện thoại/máy tính khác khi dùng IP LAN, cần cấu hình HTTPS hợp lệ cho hostname truy cập. Khi chỉ chạy HTTP bằng IP LAN, trang có thể mở được nhưng nút bật Push có thể bị trình duyệt từ chối.

## Cấu hình giờ và dữ liệu

- Django dùng `Asia/Ho_Chi_Minh` (UTC+7).
- Giờ nhắc được nhập dạng 24 giờ `HH:mm`, ví dụ `07:05`, `14:30`, `23:00`.
- Database SQLite hiện có được giữ lại trong gói. Không xóa `backend/db.sqlite3` nếu cần dữ liệu cũ.

## Chạy thủ công nếu cần

Backend: `backend\\.venv\\Scripts\\python.exe manage.py runserver 0.0.0.0:8000`

Worker: `backend\\.venv\\Scripts\\python.exe manage.py send_due_reminders`

Frontend: `cd frontend && npm run dev -- --host 0.0.0.0`

## Kiểm tra trước khi triển khai Internet

Đây là cấu hình phát triển trong mạng nội bộ: `DEBUG=True`, CORS mở cho LAN và Django development server. Không dùng trực tiếp cho Internet/public production. Khi triển khai thật cần HTTPS, production server, `DEBUG=False`, `ALLOWED_HOSTS`, CORS giới hạn, secret key mạnh và sao lưu DB.


## Bật thông báo trên máy tính và điện thoại (HTTPS)

Web Push không hoạt động trên địa chỉ HTTP bằng IP LAN (ví dụ http://192.168.x.x:5173). Bản này dùng Cloudflare Quick Tunnel để cấp URL HTTPS tạm thời và Vite proxy `/api` về Django. Cài Cloudflared một lần: `winget install --id Cloudflare.cloudflared`. Sau đó chạy `CHAY_HEALTHCARE_AI.bat`, đợi cửa sổ Tunnel hiện URL `https://....trycloudflare.com`, dùng URL đó trên máy tính và điện thoại. Mỗi thiết bị phải tự đăng nhập, bật thông báo và cấp quyền. iPhone/iPad cần iOS/iPadOS 16.4+, thêm PWA vào Màn hình chính rồi mới bật thông báo. Giữ cả bốn cửa sổ chạy. Quick Tunnel là URL tạm thời, sẽ đổi khi khởi động lại.

Lưu ý: HTTPS tunnel đưa website ra Internet qua URL tạm thời; dùng mật khẩu mạnh, không chia sẻ URL, không dùng cho dữ liệu thật nhạy cảm nếu chưa triển khai bảo mật production. Firebase Service Account JSON phải được đặt riêng trong `backend/firebase-service-account.json`, không commit/đưa lên nơi công khai.
