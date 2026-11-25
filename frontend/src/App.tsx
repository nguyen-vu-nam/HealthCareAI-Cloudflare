import { useEffect, useRef, useState } from 'react'
import {
  Activity, Bell, Bot, ChevronLeft, ChevronRight, Droplets, Footprints, HeartPulse,
  LayoutDashboard, LogIn, Menu, MoonStar, Settings, ShieldCheck, Sparkles, UserRound,
  X, ArrowRight, Send, Plus, LogOut, Moon, Sun, GlassWater, CalendarDays, Clock3
} from 'lucide-react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api, clearTokens, getToken, login, register } from './api'
import { enablePushNotifications } from './firebase'

type Page = 'dashboard'|'profile'|'water'|'sleep'|'activity'|'reminders'|'chat'|'settings'
const nav:{id:Page;label:string;icon:any}[] = [
  {id:'dashboard',label:'Tổng quan',icon:LayoutDashboard},{id:'profile',label:'Hồ sơ sức khỏe',icon:UserRound},
  {id:'water',label:'Theo dõi nước',icon:Droplets},{id:'sleep',label:'Giấc ngủ',icon:MoonStar},
  {id:'activity',label:'Vận động',icon:Footprints},{id:'reminders',label:'Nhắc nhở',icon:Bell},
  {id:'chat',label:'Trợ lý AI',icon:Bot},{id:'settings',label:'Cài đặt',icon:Settings},
]
const sampleChart = [{day:'T2',water:1500},{day:'T3',water:1800},{day:'T4',water:2100},{day:'T5',water:1700},{day:'T6',water:2000},{day:'T7',water:1800},{day:'CN',water:1800}]
const labels:Record<Page,string> = {dashboard:'Tổng quan',profile:'Hồ sơ sức khỏe',water:'Theo dõi nước uống',sleep:'Giấc ngủ',activity:'Hoạt động thể chất',reminders:'Nhắc nhở',chat:'Trợ lý AI',settings:'Cài đặt'}

export default function App(){
  const [authenticated,setAuthenticated] = useState(!!getToken())
  const [page,setPage] = useState<Page>('dashboard')
  const [mobile,setMobile] = useState(false)
  const [expanded,setExpanded] = useState(false)
  const [dark,setDark] = useState(true)
  const [authPage,setAuthPage] = useState<'login'|'register'|null>(null)
  const [username,setUsername] = useState(()=>localStorage.getItem('healthcare_ai_username') || '')
  const [email,setEmail] = useState('')
  const [password,setPassword] = useState('')
  const [fullName,setFullName] = useState('')
  const [error,setError] = useState('')
  const [notice,setNotice] = useState('')
  const [profile,setProfile] = useState<any>({})
  const [dashboard,setDashboard] = useState<any>(null)
  const [water,setWater] = useState<any[]>([])
  const [sleep,setSleep] = useState<any[]>([])
  const [activities,setActivities] = useState<any[]>([])
  const [reminders,setReminders] = useState<any[]>([])
  const [amount,setAmount] = useState('250')
  const [sleepHours,setSleepHours] = useState('7')
  const [activityType,setActivityType] = useState('walking')
  const [minutes,setMinutes] = useState('30')
  const [chatText,setChatText] = useState('')
  const [chatLoading,setChatLoading] = useState(false)
  const chatThreadRef = useRef<HTMLDivElement|null>(null)
  const [chatMessages,setChatMessages] = useState<{role:string;text:string}[]>([{role:'ai',text:'Xin chào! Tôi là trợ lý HealthCare AI. Bạn muốn tìm hiểu điều gì về sức khỏe hôm nay?'}])
  const [reminderTitle,setReminderTitle] = useState('Uống nước')
  const [reminderTime,setReminderTime] = useState('09:00')
  const [pushBusy,setPushBusy] = useState(false)
  const [dailyGoal,setDailyGoal] = useState<any>({water_ml:2000,sleep_hours:8,activity_minutes:30,alert_time:'21:00'})
  const [goalSaving,setGoalSaving] = useState(false)
  const [pushEnabled,setPushEnabled] = useState(typeof Notification !== 'undefined' && Notification.permission === 'granted')

  useEffect(()=>{setMobile(window.matchMedia('(max-width: 760px)').matches)},[])
  useEffect(()=>{if(authenticated) loadAll()},[authenticated])
  useEffect(()=>{
    if(!authenticated) return
    let cancelled = false
    api('/chat/history/').then((result:any)=>{
      if(cancelled) return
      if(Array.isArray(result.messages) && result.messages.length){
        setChatMessages(result.messages.map((m:any)=>({role:m.role,text:m.text})))
      }else{
        setChatMessages([{role:'ai',text:'Xin chào! Tôi là trợ lý HealthCare AI. Bạn muốn tìm hiểu điều gì về sức khỏe hôm nay?'}])
      }
    }).catch((e:any)=>{
      if(!cancelled) setNotice('Không tải được lịch sử chat từ máy chủ: '+e.message)
    })
    return ()=>{cancelled=true}
  },[authenticated])
  async function loadAll(){
    try{
      const [p,d,w,s,a,r,g] = await Promise.all([
        api('/profile/'),api('/dashboard/'),api('/water-logs/'),api('/sleep-logs/'),api('/activity-logs/'),api('/reminders/'),api('/daily-goal/')
      ])
      setProfile(p);setDashboard(d);setWater(w.results||w);setSleep(s.results||s);setActivities(a.results||a);setReminders(r.results||r);setDailyGoal({...g,water_ml:g.water_ml??2000,sleep_hours:g.sleep_hours??8,activity_minutes:g.activity_minutes??30,alert_time:String(g.alert_time||'21:00').slice(0,5)})
    }catch(e:any){setNotice(e.message)}
  }
  async function submitAuth(e:React.FormEvent){
    e.preventDefault();setError('')
    try{
      if(authPage==='register'){
        await register({username,email,password,full_name:fullName})
        await login(username,password)
      }else await login(username,password)
      localStorage.setItem('healthcare_ai_username', username.trim())
      // Lịch sử được tải từ database bởi useEffect sau khi xác thực thành công.
      setChatMessages([{role:'ai',text:'Xin chào! Tôi là trợ lý HealthCare AI. Bạn muốn tìm hiểu điều gì về sức khỏe hôm nay?'}])
      setAuthenticated(true);setPage('dashboard')
    }catch(e:any){setError(e.message)}
  }
  async function saveDailyGoal(e:React.FormEvent){
    e.preventDefault()

    // Ô nhập dùng đúng 4 chữ số HHMM; API/database vẫn nhận HH:MM.
    const timeDigits = String(dailyGoal.alert_time || '').replace(/\D/g, '').slice(0, 4)
    if(!/^\d{4}$/.test(timeDigits)){
      setNotice('Vui lòng nhập đủ 4 chữ số theo định dạng HHMM, ví dụ 0930.')
      return
    }
    const hours = Number(timeDigits.slice(0,2))
    const minutes = Number(timeDigits.slice(2,4))
    if(hours < 0 || hours > 23 || minutes < 0 || minutes > 59){
      setNotice('Giờ phải từ 00–23 và phút phải từ 00–59.')
      return
    }

    const apiTime = `${timeDigits.slice(0,2)}:${timeDigits.slice(2,4)}`
    setGoalSaving(true)
    try{
      const saved = await api('/daily-goal/',{method:'PATCH',body:JSON.stringify({
        water_ml:Number(dailyGoal.water_ml),sleep_hours:Number(dailyGoal.sleep_hours),
        activity_minutes:Number(dailyGoal.activity_minutes),alert_time:apiTime
      })})
      setDailyGoal({...saved,alert_time:apiTime})
      setNotice('Đã lưu mục tiêu hằng ngày')
    }catch(e:any){setNotice(e.message||'Không thể lưu mục tiêu')}
    finally{setGoalSaving(false)}
  }
  function logout(){clearTokens();setAuthenticated(false);setExpanded(false);setPage('dashboard')}
  async function saveProfile(e:React.FormEvent){
    e.preventDefault()
    try{const p=await api('/profile/',{method:'PATCH',body:JSON.stringify(profile)});setProfile(p);setNotice('Đã lưu hồ sơ');loadAll()}catch(e:any){setNotice(e.message)}
  }
  async function addWater(e:React.FormEvent){
    e.preventDefault()
    try{await api('/water-logs/',{method:'POST',body:JSON.stringify({amount_ml:Number(amount),recorded_at:new Date().toISOString()})});setAmount('250');setNotice('Đã ghi nhận nước uống');loadAll()}catch(e:any){setNotice(e.message)}
  }
  async function addSleep(e:React.FormEvent){
    e.preventDefault()
    try{await api('/sleep-logs/',{method:'POST',body:JSON.stringify({sleep_hours:Number(sleepHours),sleep_date:new Date().toISOString().slice(0,10)})});setNotice('Đã lưu nhật ký giấc ngủ');loadAll()}catch(e:any){setNotice(e.message)}
  }
  async function addActivity(e:React.FormEvent){
    e.preventDefault()
    try{await api('/activity-logs/',{method:'POST',body:JSON.stringify({activity_type:activityType,duration_minutes:Number(minutes),activity_date:new Date().toISOString().slice(0,10)})});setNotice('Đã lưu hoạt động');loadAll()}catch(e:any){setNotice(e.message)}
  }
  async function enableDeviceNotifications(){
    setPushBusy(true)
    try{
      const token = await enablePushNotifications()
      await api('/push/register/',{method:'POST',body:JSON.stringify({token,user_agent:navigator.userAgent})})
      setPushEnabled(true)
      setNotice('Đã đăng ký thiết bị nhận thông báo HealthCare AI.')
    }catch(e:any){setNotice(e.message)}
    finally{setPushBusy(false)}
  }
  async function sendTestNotification(){
    try{
      await api('/push/test/',{method:'POST',body:JSON.stringify({})})
      setNotice('Đã gửi thông báo thử nghiệm. Kiểm tra điện thoại nhé.')
    }catch(e:any){setNotice(e.message)}
  }
  async function addReminder(e:React.FormEvent){
    e.preventDefault()
    try{await api('/reminders/',{method:'POST',body:JSON.stringify({title:reminderTitle,reminder_type:'general',reminder_time:reminderTime,repeat_daily:true,enabled:true})});setNotice('Đã tạo nhắc nhở');loadAll()}catch(e:any){setNotice(e.message)}
  }
  async function sendChat(e:React.FormEvent){
    e.preventDefault();if(!chatText.trim()||chatLoading)return
    const q=chatText.trim();setChatMessages(m=>[...m,{role:'user',text:q}]);setChatText('');setChatLoading(true)
    try{
      const r=await api('/chat/',{method:'POST',body:JSON.stringify({message:q})})
      setChatMessages(m=>[...m,{role:'ai',text:r.reply||'Xin lỗi, AI chưa trả về nội dung.'}])
    }catch(e:any){
      setChatMessages(m=>[...m,{role:'ai',text:e.message||'Không thể kết nối trợ lý AI.'}])
    }finally{setChatLoading(false)}
  }
  useEffect(()=>{if(page==='chat'&&chatThreadRef.current)chatThreadRef.current.scrollTo({top:chatThreadRef.current.scrollHeight,behavior:'smooth'})},[page,chatMessages,chatLoading])
  const totalWater = water.reduce((n,x)=>n+x.amount_ml,0)
  const bmi = profile.weight_kg && profile.height_cm ? (profile.weight_kg/((profile.height_cm/100)**2)).toFixed(2) : dashboard?.bmi ?? '--'
  const waterTarget = dashboard?.water_target_ml || (profile.weight_kg ? profile.weight_kg*35 : 2000)

  if(!authenticated) return <div className="landing">
    <header className="public-header"><a className="brand" href="#"><span className="brand-icon"><HeartPulse/></span><span>HealthCare AI<small>PERSONAL HEALTH</small></span></a>
      <nav><a href="#home">Trang chủ</a><a href="#services">Dịch vụ</a><a href="#about">Giới thiệu</a><a href="#contact">Liên hệ</a></nav>
      <button className="btn btn-primary" onClick={()=>setAuthPage('login')}>Đăng nhập</button>
    </header>
    <main>
      <section className="hero" id="home"><div className="hero-copy"><span className="eyebrow"><Sparkles size={15}/> NỀN TẢNG CHĂM SÓC SỨC KHỎE TÍCH HỢP AI</span>
        <h1>Chăm sóc sức khỏe thông minh cùng <em>AI</em></h1>
        <p>Theo dõi chỉ số cơ thể, quản lý thói quen sinh hoạt và tìm hiểu kiến thức sức khỏe với trợ lý AI cá nhân.</p>
        <div className="hero-actions"><button className="btn btn-primary" onClick={()=>setAuthPage('register')}>Bắt đầu ngay <ArrowRight size={17}/></button><a className="btn btn-outline" href="#services">Khám phá dịch vụ</a></div>
        <div className="trust"><ShieldCheck size={17}/> Dữ liệu cá nhân được quản lý có kiểm soát</div>
      </div><div className="hero-chat"><div className="chat-head"><span className="bot-avatar"><Bot/></span><div><b>HealthCare AI</b><small>Trợ lý sức khỏe · Online</small></div><span className="online-dot"/></div><div className="chat-preview"><div className="bubble">Xin chào! Tôi có thể giúp bạn theo dõi thói quen sinh hoạt và tìm hiểu kiến thức sức khỏe phổ thông. Bạn muốn bắt đầu từ đâu?</div><div className="bubble bubble-user">Làm sao để sống khỏe hơn?</div><div className="bubble">Hãy bắt đầu bằng việc theo dõi giấc ngủ, uống nước và vận động đều đặn nhé!</div></div><div className="chat-input-preview">Hỏi HealthCare AI về sức khỏe... <Send size={17}/></div></div></section>
      <section className="services" id="services"><div className="section-title"><span className="eyebrow">HEALTHCARE SOLUTIONS</span><h2>Dịch vụ của chúng tôi</h2><p>Các công cụ hỗ trợ bạn chủ động chăm sóc sức khỏe mỗi ngày.</p></div><div className="service-grid">
        {[['activity','Theo dõi chỉ số','Quản lý chiều cao, cân nặng và BMI.'],['droplets','Quản lý nước uống','Ghi nhận và thống kê lượng nước mỗi ngày.'],['moon-star','Theo dõi giấc ngủ','Ghi nhận thời gian nghỉ ngơi và lịch sử ngủ.'],['bot','Trợ lý AI','Tra cứu kiến thức sức khỏe phổ thông.']].map(([ic,t,d])=><article className="service-card" key={t}><span className="service-icon">{ic==='activity'?<Activity/>:ic==='droplets'?<Droplets/>:ic==='moon-star'?<MoonStar/>:<Bot/>}</span><h3>{t}</h3><p>{d}</p></article>)}
      </div></section>
      <section className="about" id="about"><div><span className="eyebrow">ABOUT HEALTHCARE AI</span><h2>Chủ động theo dõi, an tâm chăm sóc</h2><p>HealthCare AI hỗ trợ lưu trữ thông tin sức khỏe, theo dõi thói quen và tổng hợp dữ liệu trực quan. Nội dung AI chỉ mang tính tham khảo, không thay thế chuyên gia y tế.</p><button className="btn btn-primary" onClick={()=>setAuthPage('register')}>Tạo tài khoản miễn phí</button></div><div className="about-art"><HeartPulse size={92}/><span>Healthy habits<br/>Better living</span></div></section>
    </main>
    <footer id="contact">© 2026 HealthCare AI · Nhóm 12 <span>Thông tin sức khỏe chỉ mang tính tham khảo.</span></footer>
    {authPage && <div className="modal-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget){setAuthPage(null);setError('')}}}><form className="auth-card" onSubmit={submitAuth}>
      <button type="button" className="modal-close" onClick={()=>{setAuthPage(null);setError('')}}><X/></button><span className="brand-icon auth-logo"><HeartPulse/></span><h2>{authPage==='login'?'Chào mừng trở lại':'Tạo tài khoản'}</h2><p>{authPage==='login'?'Đăng nhập để quản lý sức khỏe của bạn':'Đăng ký tài khoản HealthCare AI'}</p>
      <div className="auth-switch"><button type="button" className={authPage==='login'?'selected':''} onClick={()=>setAuthPage('login')}>Đăng nhập</button><button type="button" className={authPage==='register'?'selected':''} onClick={()=>setAuthPage('register')}>Đăng ký</button></div>
      {authPage==='register'&&<label>Họ và tên<input required value={fullName} onChange={e=>setFullName(e.target.value)} placeholder="Nguyễn Văn A"/></label>}
      <label>Tên đăng nhập<input required value={username} onChange={e=>setUsername(e.target.value)} placeholder="Tên đăng nhập"/></label>
      {authPage==='register'&&<label>Email<input type="email" required value={email} onChange={e=>setEmail(e.target.value)} placeholder="email@example.com"/></label>}
      <label>Mật khẩu<input type="password" required minLength={8} value={password} onChange={e=>setPassword(e.target.value)} placeholder="Tối thiểu 8 ký tự"/></label>
      {error&&<div className="error">{error}</div>}<button className="btn btn-primary auth-submit">{authPage==='login'?'Đăng nhập':'Tạo tài khoản'}</button>
      <small className="auth-foot">Thông tin sức khỏe của bạn chỉ được truy cập sau khi xác thực.</small>
    </form></div>}
  </div>

  return <div className={`app-shell ${dark?'dark':''}`}>
    <aside className={`sidebar ${mobile?(expanded?'mobile-expanded':'mobile-collapsed'):''}`}>
      <div className="side-brand"><span className="brand-icon"><HeartPulse/></span><div className="brand-text"><b>HealthCare AI</b><small>PERSONAL HEALTH</small></div></div>
      <button className="side-toggle" onClick={()=>setExpanded(v=>!v)} aria-label="Mở hoặc thu gọn menu"><Menu size={20}/><span>{mobile?'Danh mục':expanded?'Thu gọn':'Mở rộng'}</span></button>
      <div className="side-nav">{nav.map(n=>{const Icon=n.icon;return <button key={n.id} className={page===n.id?'active':''} onClick={()=>{setPage(n.id);if(mobile)setExpanded(false)}} title={n.label}><Icon size={19}/><span>{n.label}</span></button>})}</div>
      <div className="side-bottom"><button onClick={()=>setDark(v=>!v)}>{dark?<Sun size={18}/>:<Moon size={18}/>}<span>{dark?'Giao diện sáng':'Giao diện tối'}</span></button><button onClick={logout}><LogOut size={18}/><span>Đăng xuất</span></button></div>
    </aside>
    {mobile&&expanded&&<button className="sidebar-scrim" aria-label="Đóng menu" onClick={()=>setExpanded(false)}/>}
    <div className="main-area">
      <header className="topbar"><div className="topbar-left"><div><b>{labels[page]}</b><small>Xin chào, {profile.full_name||username||'bạn'}!</small></div></div><div className="topbar-right"><span className="date-label"><CalendarDays size={15}/> {new Date().toLocaleDateString('vi-VN')}</span><span className="user-chip"><span className="avatar">{(profile.full_name||username||'U').slice(0,1).toUpperCase()}</span><b>{profile.full_name||username||'Người dùng'}</b></span></div></header>
      <main className={`page-content ${page==='chat'?'chat-page-content':''}`}>
        {notice&&<div className="notice" onClick={()=>setNotice('')}>{notice}<button><X size={15}/></button></div>}
        {page==='dashboard'&&<><div className="welcome-row"><div><span className="eyebrow">HEALTH OVERVIEW</span><h1>Tổng quan sức khỏe</h1><p>Theo dõi các chỉ số và thói quen của bạn trong ngày.</p></div><span className="date-pill"><CalendarDays size={16}/> Hôm nay</span></div>
          <div className="stat-grid"><Stat icon={<Activity/>} label="Chỉ số BMI" value={String(bmi)} note={dashboard?.bmi_label||'Cần cập nhật hồ sơ'}/><Stat icon={<Droplets/>} label="Nước đã uống" value={`${totalWater.toLocaleString('vi-VN')} ml`} note={`Mục tiêu ${waterTarget} ml`}/><Stat icon={<MoonStar/>} label="Giấc ngủ gần nhất" value={`${sleep[0]?.sleep_hours??'--'} giờ`} note="Theo nhật ký đã ghi"/><Stat icon={<Footprints/>} label="Vận động gần nhất" value={`${activities[0]?.duration_minutes??0} phút`} note="Thời lượng hoạt động"/></div>
          <div className="content-grid"><section className="panel chart-panel"><div className="panel-heading"><div><h3>Thống kê lượng nước</h3><p>Tổng hợp theo 7 ngày gần nhất</p></div><span className="soft-tag">7 ngày</span></div><div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><BarChart data={dashboard?.daily_data?.map((x:any)=>({day:new Date(x.date).toLocaleDateString('vi-VN',{weekday:'short'}),water:x.total_water_ml}))||sampleChart}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--line)"/><XAxis dataKey="day" axisLine={false} tickLine={false}/><YAxis axisLine={false} tickLine={false}/><Tooltip/><Bar dataKey="water" name="Nước uống" fill="#65A9F6" radius={[7,7,0,0]}/></BarChart></ResponsiveContainer></div></section>
          <section className="panel quick-panel"><div className="panel-heading"><div><h3>Truy cập nhanh</h3><p>Ghi nhận hoạt động hằng ngày</p></div></div>{[['water','Uống nước',Droplets],['sleep','Giấc ngủ',MoonStar],['activity','Vận động',Footprints],['chat','Hỏi trợ lý AI',Bot]].map(([id,label,Icon]:any)=><button className="quick-link" key={id} onClick={()=>setPage(id)}><span><Icon size={18}/>{label}</span><ChevronRight size={17}/></button>)}</section></div>
        </>}
        {page==='profile'&&<section className="panel form-panel"><div className="panel-heading"><div><h3>Hồ sơ sức khỏe</h3><p>Thông tin cá nhân và chỉ số cơ thể</p></div></div><form onSubmit={saveProfile} className="form-grid"><label>Họ và tên<input value={profile.full_name||''} onChange={e=>setProfile({...profile,full_name:e.target.value})}/></label><label>Ngày sinh<input type="date" value={profile.birth_date||''} onChange={e=>setProfile({...profile,birth_date:e.target.value})}/></label><label>Giới tính<select value={profile.gender||''} onChange={e=>setProfile({...profile,gender:e.target.value})}><option value="">Chọn giới tính</option><option value="Nam">Nam</option><option value="Nữ">Nữ</option><option value="Khác">Khác</option></select></label><label>Chiều cao (cm)<input type="number" min="1" value={profile.height_cm||''} onChange={e=>setProfile({...profile,height_cm:e.target.value})}/></label><label>Cân nặng (kg)<input type="number" min="1" step=".1" value={profile.weight_kg||''} onChange={e=>setProfile({...profile,weight_kg:e.target.value})}/></label><div className="form-actions"><button className="btn btn-primary">Lưu hồ sơ</button></div></form></section>}
        {page==='water'&&<div className="two-col"><section className="panel form-panel"><h3>Ghi nhận nước uống</h3><p className="muted">Thêm lượng nước bạn vừa uống.</p><form onSubmit={addWater}><label>Lượng nước (ml)<input type="number" min="1" value={amount} onChange={e=>setAmount(e.target.value)}/></label><button className="btn btn-primary"><Plus size={17}/> Lưu bản ghi</button></form><div className="water-progress"><b>{totalWater.toLocaleString('vi-VN')} / {waterTarget} ml</b><div><span style={{width:`${Math.min(100,totalWater/waterTarget*100)}%`}}/></div></div></section><section className="panel"><h3>Lịch sử uống nước</h3>{water.slice(0,8).map(x=><div className="list-row" key={x.id}><span className="list-icon"><GlassWater/></span><div><b>{x.amount_ml} ml</b><small>{new Date(x.recorded_at).toLocaleString('vi-VN')}</small></div></div>)}{!water.length&&<Empty text="Chưa có bản ghi nước uống."/>}</section></div>}
        {page==='sleep'&&<div className="two-col"><section className="panel form-panel"><h3>Ghi nhận giấc ngủ</h3><form onSubmit={addSleep}><label>Thời lượng ngủ (giờ)<input type="number" min=".5" max="24" step=".5" value={sleepHours} onChange={e=>setSleepHours(e.target.value)}/></label><button className="btn btn-primary"><Plus size={17}/> Lưu nhật ký</button></form></section><section className="panel"><h3>Lịch sử giấc ngủ</h3>{sleep.map(x=><div className="list-row" key={x.id}><span className="list-icon purple"><MoonStar/></span><div><b>{x.sleep_hours} giờ</b><small>{x.sleep_date}</small></div></div>)}{!sleep.length&&<Empty text="Chưa có nhật ký giấc ngủ."/>}</section></div>}
        {page==='activity'&&<div className="two-col"><section className="panel form-panel"><h3>Ghi nhận hoạt động</h3><form onSubmit={addActivity}><label>Loại hoạt động<select value={activityType} onChange={e=>setActivityType(e.target.value)}><option value="walking">Đi bộ</option><option value="running">Chạy bộ</option><option value="cycling">Đạp xe</option><option value="gym">Tập gym</option><option value="yoga">Yoga</option><option value="swimming">Bơi lội</option></select></label><label>Thời lượng (phút)<input type="number" min="1" value={minutes} onChange={e=>setMinutes(e.target.value)}/></label><button className="btn btn-primary"><Plus size={17}/> Lưu hoạt động</button></form></section><section className="panel"><h3>Lịch sử vận động</h3>{activities.map(x=><div className="list-row" key={x.id}><span className="list-icon orange"><Footprints/></span><div><b>{x.duration_minutes} phút</b><small>{x.activity_date} · {x.activity_type}</small></div></div>)}{!activities.length&&<Empty text="Chưa có hoạt động."/>}</section></div>}
        {page==='reminders'&&<div className="two-col"><section className="panel form-panel"><h3>Tạo nhắc nhở</h3><form onSubmit={addReminder}><label>Tên nhắc nhở<input value={reminderTitle} onChange={e=>setReminderTitle(e.target.value)}/></label><label>Thời gian (24 giờ, HH:mm)<input type="text" inputMode="numeric" placeholder="Ví dụ: 14:30" pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$" maxLength={5} value={reminderTime} onChange={e=>setReminderTime(e.target.value.replace(/[^0-9:]/g,'').slice(0,5))} required/><small className="muted">Nhập từ 00:00 đến 23:59 theo giờ Việt Nam.</small></label><button className="btn btn-primary"><Plus size={17}/> Tạo nhắc nhở</button></form><div className="push-setup">
  <h4><Bell size={17}/> Thông báo trên thiết bị</h4>
  <p className="muted">Bật thông báo cho máy tính hoặc điện thoại. Trình duyệt cần được cấp quyền; truy cập từ thiết bị khác trong mạng LAN cần HTTPS để bật Web Push.</p>
  <button type="button" className="btn btn-primary" disabled={pushBusy} onClick={enableDeviceNotifications}>{pushBusy?'Đang đăng ký...':pushEnabled?'Đăng ký/cập nhật thiết bị':'Bật thông báo trên thiết bị'}</button>
  {pushEnabled&&<button type="button" className="btn btn-outline" onClick={sendTestNotification}>Gửi thông báo thử</button>}
</div>
<p className="muted">Lịch nhắc được lưu trong SQLite. Tiến trình reminder worker trên server phải luôn chạy để gửi đúng giờ.</p></section><section className="panel"><h3>Danh sách nhắc nhở</h3>{reminders.map(x=><div className="list-row" key={x.id}><span className="list-icon"><Bell/></span><div><b>{x.title}</b><small>{x.reminder_time} · {x.enabled?'Đang bật':'Đã tắt'}</small></div></div>)}{!reminders.length&&<Empty text="Chưa có nhắc nhở."/>}</section></div>}
        {page==='chat'&&<section className="panel chat-panel"><div className="chat-panel-head"><span className="bot-avatar chat-bot-avatar"><Bot/></span><div><b>HealthCare AI</b><small>Trợ lý kiến thức sức khỏe phổ thông</small></div><span className="online-label">● Sẵn sàng</span></div><div className="chat-thread" ref={chatThreadRef}>{chatMessages.map((m,i)=><div className={`message-row ${m.role==='user'?'from-user-row':''}`} key={i}>{m.role!=='user'&&<span className="message-avatar"><Bot size={17}/></span>}<div className={`message ${m.role==='user'?'from-user':'from-ai'}`}>{m.text}</div></div>)}{chatLoading&&<div className="message-row"><span className="message-avatar"><Bot size={17}/></span><div className="message typing-bubble" aria-label="AI đang trả lời"><span/><span/><span/></div></div>}</div><form className="chat-compose" onSubmit={sendChat}><input value={chatText} onChange={e=>setChatText(e.target.value)} placeholder="Nhập câu hỏi về sức khỏe..." disabled={chatLoading}/><button className="send-btn" disabled={chatLoading||!chatText.trim()} aria-label="Gửi câu hỏi"><Send size={18}/></button></form><p className="muted chat-disclaimer">Thông tin chỉ mang tính tham khảo, không thay thế chẩn đoán hoặc tư vấn y tế.</p></section>}
        {page==='settings'&&<div className="settings-layout">
          <section className="settings-intro"><span className="eyebrow">PERSONAL HEALTH SETTINGS</span><h1>Cài đặt cá nhân</h1><p>Thiết lập mục tiêu mỗi ngày để HealthCare AI theo dõi tiến độ và nhắc nhở phù hợp.</p></section>
          <form className="panel goal-settings-panel" onSubmit={saveDailyGoal}>
            <div className="settings-section-heading"><div><h3>Mục tiêu hằng ngày</h3><p>Các chỉ tiêu sẽ được dùng trong trang tổng quan sức khỏe.</p></div><span className="settings-heading-icon"><Activity/></span></div>
            <div className="goal-settings-grid">
              <label className="goal-setting-card goal-water"><span className="goal-setting-icon"><Droplets/></span><b>Uống nước</b><small>Lượng nước mục tiêu mỗi ngày</small><div className="goal-input-wrap"><input type="number" min="250" max="10000" step="50" value={dailyGoal.water_ml} onChange={e=>setDailyGoal({...dailyGoal,water_ml:e.target.value})} required/><span>ml/ngày</span></div></label>
              <label className="goal-setting-card goal-sleep"><span className="goal-setting-icon"><MoonStar/></span><b>Giấc ngủ</b><small>Thời lượng ngủ mong muốn</small><div className="goal-input-wrap"><input type="number" min="1" max="24" step="0.5" value={dailyGoal.sleep_hours} onChange={e=>setDailyGoal({...dailyGoal,sleep_hours:e.target.value})} required/><span>giờ/ngày</span></div></label>
              <label className="goal-setting-card goal-activity"><span className="goal-setting-icon"><Footprints/></span><b>Vận động</b><small>Thời gian hoạt động thể chất</small><div className="goal-input-wrap"><input type="number" min="1" max="1440" step="1" value={dailyGoal.activity_minutes} onChange={e=>setDailyGoal({...dailyGoal,activity_minutes:e.target.value})} required/><span>phút/ngày</span></div></label>
              <label className="goal-setting-card goal-reminder"><span className="goal-setting-icon"><Bell/></span><b>Giờ nhắc nhở</b><small>Nhập giờ và phút theo định dạng 24 giờ</small><div className="goal-input-wrap"><input
                type="text"
                inputMode="numeric"
                autoComplete="off"
                placeholder="HH:MM"
                aria-label="Giờ nhắc nhở, định dạng HH:MM"
                maxLength={5}
                value={dailyGoal.alert_time || ''}
                onChange={e => {
                  const input = e.currentTarget
                  const cursor = input.selectionStart ?? input.value.length
                  const digitsBeforeCursor = input.value.slice(0, cursor).replace(/\D/g, '').length
                  const digits = input.value.replace(/\D/g, '').slice(0, 4)
                  const formatted = digits.length > 2
                    ? `${digits.slice(0, 2)}:${digits.slice(2)}`
                    : digits

                  setDailyGoal({ ...dailyGoal, alert_time: formatted })

                  // Giữ con trỏ đúng vị trí sau khi tự chèn dấu hai chấm.
                  const nextCursor = digitsBeforeCursor > 2
                    ? digitsBeforeCursor + 1
                    : digitsBeforeCursor
                  requestAnimationFrame(() => {
                    input.setSelectionRange(nextCursor, nextCursor)
                  })
                }}
                onBlur={() => {
                  const digits = String(dailyGoal.alert_time || '').replace(/\D/g, '')
                  if (digits.length === 4) {
                    const hh = Number(digits.slice(0, 2))
                    const mm = Number(digits.slice(2, 4))
                    if (hh > 23 || mm > 59) {
                      setNotice('Giờ hợp lệ từ 00–23 và phút từ 00–59.')
                    }
                  }
                }}
                required
              /><span>24 giờ</span></div><small>Giờ 00–23 · Phút 00–59 · Ví dụ 09:30</small></label>
            </div>
            <div className="settings-form-actions"><span>Lưu thay đổi để cập nhật mục tiêu trên toàn hệ thống.</span><button className="btn btn-primary" disabled={goalSaving}>{goalSaving?'Đang lưu...':'Lưu mục tiêu'}</button></div>
          </form>
          <section className="panel settings-account-panel"><div className="setting-row"><div><b>Giao diện tối</b><small>Điều chỉnh giao diện ứng dụng</small></div><button type="button" className="btn btn-outline" onClick={()=>setDark(v=>!v)}>{dark?'Tắt chế độ tối':'Bật chế độ tối'}</button></div><div className="setting-row"><div><b>Tài khoản</b><small>{username}</small></div><button type="button" className="btn btn-outline" onClick={logout}>Đăng xuất</button></div></section>
        </div>}
      </main>
    </div>
  </div>
}

function Stat({icon,label,value,note}:any){return <div className="stat-card"><span className="stat-icon">{icon}</span><span className="stat-label">{label}</span><strong>{value}</strong><small>{note}</small></div>}
function Empty({text}:{text:string}){return <div className="empty-state">{text}</div>}
