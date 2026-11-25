@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title HealthCare AI - Khoi dong HTTPS Push

echo ==================================================
echo       HEALTHCARE AI - HTTPS + FIREBASE PUSH
echo ==================================================
echo.
if not exist "backend\manage.py" (echo [LOI] Khong tim thay backend\manage.py & pause & exit /b 1)
if not exist "frontend\package.json" (echo [LOI] Khong tim thay frontend\package.json & pause & exit /b 1)
where py >nul 2>nul || (echo [LOI] Can Python Launcher va Python 3.11 & pause & exit /b 1)
where npm >nul 2>nul || (echo [LOI] Can cai Node.js LTS & pause & exit /b 1)
where cloudflared >nul 2>nul
if errorlevel 1 (
  echo [LOI] Chua tim thay cloudflared.
  echo Cai mot lan bang lenh: winget install --id Cloudflare.cloudflared
  echo Sau khi cai xong, dong CMD va mo lai file BAT.
  pause
  exit /b 1
)
if not exist "backend\.venv\Scripts\python.exe" (
  py -3.11 -m venv backend\.venv || (echo [LOI] Tao Python venv that bai & pause & exit /b 1)
)
if not exist "backend\.env" copy "backend\.env.example" "backend\.env" >nul
if not exist "frontend\.env" copy "frontend\.env.example" "frontend\.env" >nul
"backend\.venv\Scripts\python.exe" -m pip install -r backend\requirements.txt || (echo [LOI] Cai thu vien Backend that bai & pause & exit /b 1)
if not exist "frontend\node_modules\vite" (
  pushd frontend
  call npm install
  if errorlevel 1 (popd & echo [LOI] npm install that bai & pause & exit /b 1)
  popd
)
"backend\.venv\Scripts\python.exe" backend\manage.py migrate --noinput || (echo [LOI] Migration that bai & pause & exit /b 1)
start "HealthCare AI - Backend API" cmd /k "cd /d ""%~dp0backend"" && .venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000"
timeout /t 3 /nobreak >nul
start "HealthCare AI - Reminder Worker" cmd /k "cd /d ""%~dp0backend"" && .venv\Scripts\python.exe manage.py send_due_reminders"
start "HealthCare AI - Frontend" cmd /k "cd /d ""%~dp0frontend"" && npm run dev -- --host 0.0.0.0"
timeout /t 5 /nobreak >nul
echo.
echo [HTTPS] Dang tao duong dan HTTPS cong khai tam thoi.
echo Hay doi dong TryCloudflare URL co dang https://....trycloudflare.com
 echo Copy URL nay mo tren ca may tinh va dien thoai.
echo Khong su dung lai dia chi http://192.168.x.x:5173 de bat Push.
start "HealthCare AI - HTTPS Tunnel" cmd /k "cloudflared tunnel --url http://127.0.0.1:5173"
echo.
echo Backend, Worker, Frontend va HTTPS Tunnel dang chay.
echo Trong cua so Tunnel, copy URL https://....trycloudflare.com de truy cap.
echo Lan dau tren moi thiet bi: mo URL HTTPS, dang nhap, vao Nhac nho, bam Bat thong bao.
echo iPhone: them website vao Man hinh chinh truoc khi cap quyen thong bao.
echo Tat he thong: dong cac cua so Backend, Worker, Frontend va Tunnel.
pause
endlocal
