'use client';
import {useEffect,useState} from 'react';
import {api} from './api';

export function AcademyEnding({stageId}:{stageId:string}){
 const [ending,setEnding]=useState<{title:string;text:string}|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 async function reveal(){setBusy(true);setError('');try{setEnding(await api('/stages/'+stageId+'/academy-ending'));}catch(e:any){setError(e.message);}finally{setBusy(false);}}
 return <div className="spaced">{ending?<section className="academy-ending" aria-live="polite"><span className="eyebrow">Архив Null / рассекречено</span><h2>{ending.title}</h2><p>{ending.text}</p></section>:<button className="btn" disabled={busy} onClick={reveal}>{busy?'Открываем архив…':'Открыть финал приключения'}</button>}{error&&<p className="error">{error}</p>}</div>;
}

export default function AcademyProgress({stageId,tasks,revision,onSelect}:{stageId:string;tasks:any[];revision:string;onSelect:(id:string)=>void}){
 const [completed,setCompleted]=useState<number[]>([]),[unlocked,setUnlocked]=useState(false),[error,setError]=useState('');
 useEffect(()=>{let live=true;api('/stages/'+stageId+'/academy-progress').then(p=>{if(live){setCompleted(p.completed_chapters);setUnlocked(p.ending_unlocked);setError('');}}).catch(e=>{if(live)setError(e.message);});return()=>{live=false;};},[stageId,revision]);
 return <section className="academy-progress spaced"><div className="row between"><div><span className="eyebrow">Миссия / Академия Алгоритмов</span><strong>Твой прогресс</strong></div><span className="badge">Пройдено {completed.length} из {tasks.filter(t=>t.academy_chapter).length} глав</span></div><details><summary>Пройденные главы</summary><div className="academy-checkpoints">{tasks.filter(t=>t.academy_chapter).map(task=>{const ch={chapter:task.academy_chapter,title:task.title},done=completed.includes(ch.chapter);return <button key={ch.chapter} type="button" disabled={!task} className={done?'checkpoint done':'checkpoint'} onClick={()=>task&&onSelect(task.id)} aria-label={'Задание '+task.position+': '+ch.title+(done?' — пройдена':'')}><span>{done?'✓':String(task.position).padStart(2,'0')}</span>{ch.title}</button>;})}</div></details><p className="small muted">Зачёт главы — принятое решение на всех проверках. Можно решать в любом порядке. Архив Null откроется после «Последнего протокола».</p>{unlocked&&<AcademyEnding stageId={stageId}/>} {error&&<p className="error">{error}</p>}</section>;
}
