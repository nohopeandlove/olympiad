'use client';
import Link from 'next/link';
import {useEffect,useState} from 'react';
import {api} from './api';
export default function Nav(){
 const [user,setUser]=useState<{role:string}|null>(null);
 useEffect(()=>{api('/profile').then(d=>setUser(d.user)).catch(()=>{});},[]);
 return <header><nav className="nav"><Link className="brand" href="/"><b>py</b> · олимпиада</Link><div className="navlinks"><Link className="optional" href="/schedule">Расписание</Link><Link href="/results">Результаты</Link>{user?.role==='admin'&&<Link href="/admin">Администратор</Link>}<Link className="btn secondary" href={user?'/dashboard':'/login'}>{user?'Личный кабинет':'Войти'}</Link></div></nav></header>
}
