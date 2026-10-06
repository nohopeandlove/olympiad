'use client';
import {useState} from 'react';
import Link from 'next/link';
import {api} from '@/components/api';
export default function Verify(){const [message,setMessage]=useState('Нажмите кнопку, чтобы подтвердить email.'),[done,setDone]=useState(false);async function verify(){try{const token=new URLSearchParams(window.location.search).get('token');if(!token)throw new Error('Ссылка недействительна');const r=await api('/auth/verify?token='+encodeURIComponent(token),{method:'POST'});setMessage(r.message);setDone(true);window.history.replaceState(null,'','/verify');}catch(e:any){setMessage(e.message);}}return <main className="container"><h1>Подтверждение email</h1><p>{message}</p>{!done&&<button className="btn" onClick={verify}>Подтвердить email</button>} {done&&<Link className="btn" href="/login">Войти</Link>}</main>}
