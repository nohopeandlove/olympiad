let identity:Promise<string>|undefined;
function examIdentity():Promise<string>{
 if(identity)return identity;
 identity=new Promise(resolve=>{
  let token=sessionStorage.getItem('exam_session')||crypto.randomUUID();
  sessionStorage.setItem('exam_session',token);
  if(typeof BroadcastChannel==='undefined'){resolve(token);return;}
  const channel=new BroadcastChannel('olympiad-tabs');const instance=crypto.randomUUID();
  channel.onmessage=({data})=>{
   if(data.type==='ping'&&data.token===token&&data.instance!==instance)channel.postMessage({type:'occupied',token,recipient:data.instance});
   if(data.type==='occupied'&&data.token===token&&data.recipient===instance){token=crypto.randomUUID();sessionStorage.setItem('exam_session',token);}
  };
  channel.postMessage({type:'ping',token,instance});
  setTimeout(()=>resolve(token),75);
 });
 return identity;
}
export async function api(path:string, options:RequestInit={}) {
  const headers=new Headers(options.headers);
  headers.set('X-Exam-Session',await examIdentity());
  if(options.body) headers.set('Content-Type','application/json');
  if(options.method && options.method!=='GET') headers.set('X-CSRF-Token',sessionStorage.getItem('csrf')||'');
  const r=await fetch('/api'+path,{...options,headers,credentials:'same-origin',cache:'no-store'});
  const data=await r.json().catch(()=>({}));
  if(!r.ok) throw new Error(typeof data.detail==='string'?data.detail:JSON.stringify(data.detail||'Ошибка запроса'));
  if(data.csrf) sessionStorage.setItem('csrf',data.csrf);
  return data;
}
export const date=(value:string)=>new Date(value).toLocaleString('ru-RU',{timeZone:'Asia/Yekaterinburg',day:'numeric',month:'long',hour:'2-digit',minute:'2-digit'});
export const statusLabel:Record<string,string>={draft:'Черновик',scheduled:'Запланирована',active:'Олимпиада открыта',finished:'Завершена'};
export const json=(data:unknown)=>JSON.stringify(data);

export const answerStatus=(s:string)=>({'Pending Review':'Ожидает оценки преподавателя',Reviewed:'Проверено преподавателем',Accepted:'Принято','Wrong Answer':'Неверный ответ',Queued:'В очереди',Running:'Проверяется'} as Record<string,string>)[s]||s;
