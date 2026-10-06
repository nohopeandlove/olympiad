'use client';
import {use,useEffect,useState} from 'react';
import Link from 'next/link';
import Markdown from 'react-markdown';
import {api,date,statusLabel} from '@/components/api';
export default function Page({params}:{params:Promise<{id:string}>}){
 const {id}=use(params); const [o,setO]=useState<any>(null),[error,setError]=useState('');
 useEffect(()=>{api('/olympiads/'+id).then(setO).catch(e=>setError(e.message));},[id]);
 return <main className="container">{error&&<div className="error">{error}</div>}{o&&<><span className="badge">{statusLabel[o.status]}</span><h1>{o.title}</h1><p className="muted">{o.description}</p><div className="grid2"><section className="card"><h2>Расписание</h2><p>Регистрация: {date(o.registration_start)} — {date(o.registration_end)}</p>{o.stages.map((s:any)=><p key={s.id}><strong>{s.title}</strong><br/>{date(s.starts_at)} — {date(s.ends_at)}<br/><span className="muted">Продолжительность: {s.duration_minutes} минут</span></p>)}<Link className="btn" href={'/register/'+id}>Зарегистрироваться</Link></section><section id="rules" className="card markdown"><h2>Правила олимпиады</h2><Markdown>{o.rules}</Markdown><p className="muted">{o.type==='SCHOOL'?'Допустимые классы: '+o.allowed_classes.join(', '):'Для студентов СПО 1 и 2 курса.'}</p></section></div></>}</main>
}
