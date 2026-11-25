// Khi truy cập bằng localhost hoặc IP LAN, API tự dùng cùng hostname với frontend.
const API = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')
export function getToken(){ return localStorage.getItem('hc_access') }
export function setTokens(access:string, refresh:string){ localStorage.setItem('hc_access',access); localStorage.setItem('hc_refresh',refresh) }
export function clearTokens(){ localStorage.removeItem('hc_access'); localStorage.removeItem('hc_refresh') }
export async function api(path:string, options:RequestInit = {}) {
  const token = getToken()
  const headers:Record<string,string> = {'Content-Type':'application/json', ...(options.headers as Record<string,string> || {})}
  if(token) headers.Authorization = `Bearer ${token}`
  const response = await fetch(`${API}${path}`, {...options, headers})
  const data = await response.json().catch(()=>({}))
  if(!response.ok) throw new Error(data.detail || Object.values(data).flat().join(' ') || 'Có lỗi xảy ra')
  return data
}
export async function login(username:string,password:string){
  const res = await api('/auth/token/',{method:'POST',body:JSON.stringify({username,password})})
  setTokens(res.access,res.refresh); return res
}
export async function register(payload:Record<string,string>){
  return api('/auth/register/',{method:'POST',body:JSON.stringify(payload)})
}
