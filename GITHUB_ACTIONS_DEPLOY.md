# HealthCareAI: phát triển trên Windows, build/deploy bằng GitHub Actions

## 1. Mô hình

- Windows: chỉnh sửa source, chạy frontend và backend local.
- GitHub Actions (Ubuntu runner): build React, kiểm tra Django, đóng gói Python Worker và deploy.
- Cloudflare: Worker `healthcareai`, frontend assets, D1 `healthcareai-db` (binding `DB`) và Cron.

Không cần WSL hoặc Docker trên máy Windows.

## 2. Tạo repository GitHub

1. Tạo repository mới trên GitHub, ví dụ `HealthCareAI-Cloudflare`.
2. Giải nén thư mục dự án này và mở CMD tại thư mục chứa `package.json`.
3. Khởi tạo Git và push nhánh `main`:

```cmd
git init
git add .
git commit -m "Prepare HealthCareAI Cloudflare deployment"
git branch -M main
git remote add origin https://github.com/USERNAME/HealthCareAI-Cloudflare.git
git push -u origin main
```

Thay `USERNAME` bằng tài khoản GitHub của mày. Không commit `.env`, Firebase service-account JSON, token hoặc key riêng. `.gitignore` đã loại các file này và SQLite local khỏi Git.

## 3. Thêm GitHub Actions secrets

Vào repository → Settings → Secrets and variables → Actions → New repository secret.

Bắt buộc:

- `CLOUDFLARE_API_TOKEN`: API token giới hạn đúng Cloudflare account, tối thiểu có quyền Workers Scripts:Edit và quyền Account Settings:Read theo yêu cầu Wrangler. Chỉ cấp D1:Edit nếu sau này workflow được bổ sung bước chạy migration D1.
- `CLOUDFLARE_ACCOUNT_ID`: `6845e8618c7afb007b39ff5e46bd2aee` (đã gắn trong cấu hình hiện tại; secret giúp Wrangler xác thực rõ ràng trong CI).
- `DJANGO_SECRET_KEY`: chuỗi bí mật ngẫu nhiên dài, chỉ dùng cho Django production.

Tuỳ chọn cho chatbot:

- `AI_API_BASE_URL`: endpoint tương thích OpenAI Chat Completions (không thêm `/chat/completions` nếu backend tự nối).
- `AI_API_KEY`: API key của nhà cung cấp AI.
- `AI_MODEL`: tên model.

Không đưa các giá trị trên vào source code hoặc commit lên GitHub. Nếu API token cũ từng xuất hiện trong file hoặc chat, hãy thu hồi và tạo token mới.

## 4. Quy trình workflow

- Mỗi lần push lên `main`, workflow tự build frontend, đóng gói dependencies Python bằng `pywrangler sync`, biên dịch mã backend và chạy Django system check.
- Deploy được tách riêng và mặc định KHÔNG tự chạy.
- Khi đã chuẩn bị xong D1 schema và secrets, vào GitHub → Actions → `HealthCareAI - Validate and Deploy` → Run workflow → chọn `deploy = true`.

Cách tách này giúp tránh deploy nhầm trước khi database có schema.

## 5. D1 và trạng thái chức năng

D1 hiện vẫn là database mới, không import dữ liệu từ SQLite cũ. Workflow KHÔNG tự chạy migration. Các migration Django hiện nằm trong `backend/health/migrations/`; cần xác minh cách chuyển/chạy chúng tương thích `django-cf` và D1 trước khi bật deploy. Không chạy `wrangler d1 migrations apply` với thư mục migration mặc định nếu chưa có file SQL D1 tương ứng.

D1 backend của `django-cf` không hỗ trợ transaction thực sự; cần rà soát các luồng ghi nhiều bảng trước khi dùng production.

## 6. Giới hạn còn lại cần xử lý trước khi dùng đầy đủ

- Firebase Push: Admin SDK chưa được xác nhận tương thích Python Workers. Cloudflare adapter hiện trả thông báo rõ ràng và không cố import `firebase_admin`; Push chưa hoạt động trên Cloudflare. Cần port sang FCM HTTP v1/Workers Fetch và kiểm thử riêng.
- AI Chat: code đã đọc cấu hình AI từ Worker bindings/secrets thay vì chỉ `os.getenv`. Tuy nhiên, request outbound hiện vẫn dùng Python `requests`; cần kiểm thử trên Pyodide/Workers và có thể phải chuyển sang Workers Fetch API trước khi xác nhận chatbot production.
- Cron chạy mỗi phút, nhưng nhắc nhở chỉ gửi được sau khi Push adapter được tích hợp.
- `DJANGO_ALLOWED_HOSTS` cho phép hostname `*.workers.dev`; nếu dùng custom domain, bổ sung hostname đó trong `wrangler.jsonc`.
- Chưa tạo tài khoản admin Django và chưa khởi tạo schema D1.

## 7. Phát triển frontend trên Windows

```cmd
npm ci --prefix frontend
npm --prefix frontend run dev
```

Build kiểm tra thủ công:

```cmd
npm --prefix frontend run build
```

Không chạy `uv run pywrangler dev` trên Windows trong giai đoạn này; workflow Ubuntu thực hiện đóng gói Python Worker và deploy.


## 8. Điều kiện trước lần deploy đầu tiên

- GitHub Actions phải có lần chạy `validate` màu xanh (bao gồm bước `pywrangler sync`).
- Đã tạo GitHub Actions secrets bắt buộc.
- D1 schema đã được tạo và kiểm tra riêng. Workflow hiện **không tự migrate D1**, không nhập dữ liệu SQLite cũ và không xóa database.
- Firebase Push và AI Chat chưa được xác nhận production-ready trên Workers; xem mục 6.
