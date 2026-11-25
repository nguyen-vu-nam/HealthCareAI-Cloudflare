importScripts('https://www.gstatic.com/firebasejs/10.14.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.14.1/firebase-messaging-compat.js');
firebase.initializeApp({
  apiKey: "AIzaSyACFUMsjTH8RhxTtq1vA9CU_AskM8_kE6c",
  authDomain: "healthcareai-2cc2a.firebaseapp.com",
  projectId: "healthcareai-2cc2a",
  storageBucket: "healthcareai-2cc2a.firebasestorage.app",
  messagingSenderId: "394540403632",
  appId: "1:394540403632:web:7956905274f155cfa8a475"
});
const messaging = firebase.messaging();
messaging.onBackgroundMessage((payload) => {
  const data = payload.data || {};
  const title = data.title || 'HealthCare AI';
  return self.registration.showNotification(title, {
    body: data.body || 'Bạn có một lời nhắc mới.',
    icon: '/icons/healthcare-icon-192.png',
    tag: `healthcare-${Date.now()}`,
    data: { url: data.url || '/' }
  });
});
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = event.notification.data?.url || '/';
  event.waitUntil(clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windows) => {
    for (const client of windows) {
      if ('focus' in client) { client.navigate(url); return client.focus(); }
    }
    return clients.openWindow(url);
  }));
});
