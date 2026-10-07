'use client';
import {useEffect,useState} from 'react';
import {api} from './api';
import {duration,elapsed} from './useTaskTiming';
export default function StudentTaskTimes({stageId}:{stageId:string}){
 const [open,setOpen]=useState(false),[data,setData]=useState<any>(null),[error,setError]=useState(''),[clock,setClock]=useState(Date.now());
 useEffect(()=>{if(!open)return;let live=true;const load=()=>api('/stages/'+stageId+'/task-times').then(r=>{if(live){setData({...r,received:Date.now()});setError('');}}).catch(e=>{if(live)setError(e.message);});load();const refresh=setInterval(load,15000),tick=setInterval(()=>setClock(Date.now()),1000);return()=>{live=false;clearInterval(refresh);clearInterval(tick);};},[stageId,open]);
 return <details onToggle={e=>setOpen(e.currentTarget.open)}><summary>Моё время по заданиям</summary>{error&&<p className="error">{error}</p>}{data?.timings.length?<ul>{data.timings.map((row:any)=><li key={row.task_id}>{row.task_title}: <strong>{duration(elapsed(row,data.server_time,data.received,clock))}</strong></li>)}</ul>:<p className="muted small">Вы ещё не открывали задания.</p>}</details>;
}
