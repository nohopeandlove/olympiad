import {answerStatus} from './api';
export default function CheckResult({result}:{result:any}){
 if(!result)return <p className="muted small">«Проверить на примерах» запускает программу без начисления баллов. «Отправить решение» проверяет все тесты и начисляет баллы.</p>;
 return <div className="console"><strong>{answerStatus(result.status)}</strong><p>{result.mode==='run'?'Запуск на примерах — без начисления баллов':`${result.score} баллов`}</p>{result.result?.message&&<p>{result.result.message}</p>}{typeof result.result?.passed==='number'&&<p>Пройдено тестов: {result.result.passed} из {result.result.tests?.length||0}</p>}{result.result?.tests?.length>0&&<details><summary>Результаты тестов</summary><ol>{result.result.tests.map((t:any,i:number)=><li key={i}>{answerStatus(t.status)}{t.stdout&&<pre>{t.stdout}</pre>}{t.stderr&&<pre>{t.stderr}</pre>}</li>)}</ol></details>}</div>;
}
