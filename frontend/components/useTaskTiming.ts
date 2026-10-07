'use client';
import {useEffect,useRef,useState} from 'react';
import {api,json} from './api';
export const duration=(ms:number)=>{const n=Math.floor(Math.max(0,ms)/1000);return [Math.floor(n/3600),Math.floor(n%3600/60),n%60].map(v=>String(v).padStart(2,'0')).join(':');};
export function elapsed(row:any,serverTime:string,received:number,clock:number){if(!row)return 0;const extra=row.active_until?Math.max(0,Math.min(clock-received,new Date(row.active_until).getTime()-new Date(serverTime).getTime())):0;return row.elapsed_ms+extra;}
export default function useTaskTiming(stageId:string,taskId:string){
 const [state,setState]=useState<any>({timings:[],server_time:'',received:Date.now()}),[clock,setClock]=useState(Date.now()),[error,setError]=useState('');
 const queue=useRef<Promise<void>>(Promise.resolve());
 useEffect(()=>{if(!taskId)return;let live=true;
  const send=(selected:string|null)=>{queue.current=queue.current.catch(()=>{}).then(async()=>{try{const data=await api('/stages/'+stageId+'/task-focus',{method:'POST',body:json({task_id:selected}),keepalive:true});if(live){setState({...data,received:Date.now()});setError('');}}catch{if(live)setError('Учёт времени приостановлен: проверьте соединение');}});};
  const sync=()=>send(!document.hidden&&document.hasFocus()&&navigator.onLine?taskId:null);
  sync();const heartbeat=setInterval(sync,15000);
  document.addEventListener('visibilitychange',sync);window.addEventListener('focus',sync);window.addEventListener('blur',sync);window.addEventListener('online',sync);window.addEventListener('offline',sync);
  return()=>{live=false;clearInterval(heartbeat);document.removeEventListener('visibilitychange',sync);window.removeEventListener('focus',sync);window.removeEventListener('blur',sync);window.removeEventListener('online',sync);window.removeEventListener('offline',sync);send(null);};
 },[stageId,taskId]);
 useEffect(()=>{const timer=setInterval(()=>setClock(Date.now()),1000);return()=>clearInterval(timer);},[]);
 const row=state.timings.find((t:any)=>t.task_id===taskId);
 return {time:duration(elapsed(row,state.server_time,state.received,clock)),running:!!row?.active_until&&clock-state.received<new Date(row.active_until).getTime()-new Date(state.server_time).getTime(),error};
}
