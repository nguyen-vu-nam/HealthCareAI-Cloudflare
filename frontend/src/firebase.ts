import { initializeApp, getApps } from 'firebase/app'
import { getMessaging, getToken, isSupported, onMessage } from 'firebase/messaging'

const config = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

let foregroundListenerReady = false

export async function enablePushNotifications(): Promise<string> {
  return getPushToken(true)
}

export async function getExistingPushToken(): Promise<string | null> {
  if (!window.isSecureContext || !("Notification" in window) || Notification.permission !== "granted") return null
  try { return await getPushToken(false) } catch { return null }
}

async function getPushToken(askPermission: boolean): Promise<string> {
  if (!window.isSecureContext) {
    throw new Error('Địa chỉ hiện tại chưa an toàn để bật thông báo. Hãy mở website bằng đường dẫn HTTPS do file BAT cung cấp, không dùng http://192.168.x.x.');
  }
  if (!('Notification' in window)) throw new Error('Thiết bị/trình duyệt này không cung cấp API thông báo. Hãy dùng Chrome hoặc Edge mới trên Windows/Android; iPhone cần cài website vào Màn hình chính.')
  if (!('serviceWorker' in navigator)) throw new Error('Trình duyệt không hỗ trợ Service Worker.')
  if (!await isSupported()) throw new Error('Trình duyệt này không hỗ trợ Firebase Web Push. Hãy cập nhật Chrome/Edge và bật quyền thông báo của hệ điều hành.')
  const required = Object.values(config).every(Boolean) && Boolean(import.meta.env.VITE_FIREBASE_VAPID_KEY)
  if (!required) throw new Error('Thiếu cấu hình Firebase trong frontend/.env.')
  const permission = askPermission ? await Notification.requestPermission() : Notification.permission
  if (permission !== 'granted') throw new Error('Bạn chưa cấp quyền thông báo. Hãy cho phép thông báo trong cài đặt website của trình duyệt.')
  const registration = await navigator.serviceWorker.register('/firebase-messaging-sw.js')
  await navigator.serviceWorker.ready
  const app = getApps().length ? getApps()[0] : initializeApp(config)
  const messaging = getMessaging(app)
  if (!foregroundListenerReady) {
    onMessage(messaging, async (payload) => {
      const title = payload.data?.title || payload.notification?.title || 'HealthCare AI'
      const body = payload.data?.body || payload.notification?.body || 'Bạn có một lời nhắc mới.'
      const reg = await navigator.serviceWorker.getRegistration()
      if (reg && Notification.permission === 'granted') {
        await reg.showNotification(title, { body, icon: '/icons/healthcare-icon-192.png', tag: `hc-${title}-${body}` })
      }
    })
    foregroundListenerReady = true
  }
  const token = await getToken(messaging, {
    vapidKey: import.meta.env.VITE_FIREBASE_VAPID_KEY,
    serviceWorkerRegistration: registration,
  })
  if (!token) throw new Error('Firebase chưa cấp được mã nhận thông báo cho thiết bị này. Kiểm tra VAPID key và cấu hình Firebase Cloud Messaging.')
  return token
}
