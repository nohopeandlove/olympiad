'use client';
import Editor,{loader} from '@monaco-editor/react';
loader.config({paths:{vs:'/monaco/vs'}});
export default function CodeEditor({value,onChange}:{value:string;onChange:(value:string|undefined)=>void}){return <Editor height="420px" language="python" theme="vs-dark" value={value} onChange={onChange} options={{fontSize:14,minimap:{enabled:false},automaticLayout:true,scrollBeyondLastLine:false,tabSize:4,padding:{top:16},wordWrap:'on'}}/>}
