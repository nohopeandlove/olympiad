// UI checks use controlled exam responses: the live official stages may be scheduled.
// Real grading, session checks and timing are exercised by backend integration tests.
import {test,expect,type Page} from '@playwright/test';
const PASSWORD='DevOnly!Python2026';
async function exam(page:Page,tasks:any[]){
 await page.goto('/login');await page.getByLabel('Email',{exact:true}).fill('school@example.org');await page.getByLabel('Пароль',{exact:true}).fill(PASSWORD);await page.getByRole('button',{name:'Войти',exact:true}).click();await expect(page).toHaveURL(/dashboard/);
 const profile=await(await page.request.get('/api/profile')).json(),sid=profile.registrations[0].stages[0].id;
 const drafts:Record<string,string>={};
 await page.route('**/api/stages/'+sid+'/start',r=>r.fulfill({json:{deadline:new Date(Date.now()+3600000).toISOString(),server_time:new Date().toISOString()}}));
 await page.route('**/api/stages/'+sid+'/tasks',r=>r.fulfill({json:tasks}));
 await page.route('**/api/stages/'+sid+'/task-focus',r=>r.fulfill({json:{timings:[],server_time:new Date().toISOString()}}));
 await page.route('**/api/anti-cheat/*',r=>r.fulfill({json:{saved:true}}));
 await page.route('**/api/tasks/*/draft',r=>{const id=r.request().url().split('/').at(-2)!;if(r.request().method()==='PUT'){drafts[id]=r.request().postDataJSON().code;return r.fulfill({json:{saved:true}});}return r.fulfill({json:{code:drafts[id]||''}});});
 await page.goto('/exam/'+sid);return sid;
}

test('Программа: редактор и понятный результат без технического JSON',async({page})=>{
 const tasks=[{id:'code-task',kind:'code',title:'Код от двери',statement:'Выведите 1.',points:100,time_limit:2,memory_limit:128,input_description:'',output_description:'1',constraints:'',examples:[],academy_chapter:null}];await exam(page,tasks);
 let body:any;
 await page.route('**/api/tasks/code-task/submissions',r=>{body=r.request().postDataJSON();return r.fulfill({status:202,json:{id:'job',task_id:'code-task',status:'Queued',score:0,mode:'submit'}});});
 await page.route('**/api/submissions/job',r=>r.fulfill({json:{id:'job',task_id:'code-task',status:'Accepted',score:100,mode:'submit',result:{passed:2,tests:[{status:'Accepted'},{status:'Accepted'}]}}}));
 await expect(page.locator('.monaco-editor')).toBeVisible();await page.locator('.monaco-editor textarea').focus();await page.keyboard.press('Control+A');await page.keyboard.type('print(1)');await page.getByRole('button',{name:'Отправить решение',exact:true}).click();await expect(page.locator('.console')).toContainText('Принято');await expect(page.locator('.console')).toContainText('100 баллов');await expect(page.locator('.console')).not.toContainText('"tests"');expect(body).toEqual({code:'print(1)',mode:'submit'});await expect(page.getByRole('button',{name:'Проверить на примерах',exact:true})).toBeVisible();
});

test('Контрольные вопросы: выбор ответа и письменный черновик',async({page})=>{
 const tasks:any[]=[{id:'choice-task',kind:'choice',title:'Панель двери',statement:'Выберите команду для целого числа.',points:30,answer_options:['int(input())','input()'],examples:[],academy_chapter:null},{id:'text-task',kind:'text',title:'Архив уровней',statement:'Объясните повторения.',points:50,answer_options:[],examples:[],academy_chapter:null}];const sid=await exam(page,tasks);let choice:any,text:any;
 await page.route('**/api/tasks/*/answers',r=>{const id=r.request().url().split('/').at(-2)!,data=r.request().postDataJSON();if(id==='choice-task')choice=data;else text=data;const sub={id:'answer-'+id,task_id:id,code:id==='choice-task'?String(data.option_index):data.answer,mode:'submit',status:id==='choice-task'?'Accepted':'Pending Review',score:id==='choice-task'?30:0};tasks.find(t=>t.id===id).my_submission=sub;return r.fulfill({status:201,json:sub});});
 await page.getByRole('radio',{name:'int(input())',exact:true}).check();page.once('dialog',d=>d.accept());await page.getByRole('button',{name:'Отправить ответ',exact:true}).click();await expect(page.locator('.editorpanel .notice')).toContainText('Принято · 30 / 30');expect(choice).toEqual({option_index:0});await expect(page.getByRole('button',{name:'Отправить ответ',exact:true})).toBeDisabled();
 await page.locator('.taskbutton').filter({hasText:'Архив уровней'}).click();const answer=page.getByRole('textbox',{name:'Развёрнутый ответ',exact:true});await answer.fill('Повторения не создают новый уровень.');const saved=page.waitForResponse(r=>r.url().endsWith('/draft')&&r.request().method()==='PUT');await saved;await page.reload();await page.locator('.taskbutton').filter({hasText:'Архив уровней'}).click();await expect(answer).toHaveValue('Повторения не создают новый уровень.');page.once('dialog',d=>d.accept());await page.getByRole('button',{name:'Отправить ответ',exact:true}).click();expect(text).toEqual({answer:'Повторения не создают новый уровень.'});await expect(page.locator('.editorpanel .notice')).toContainText('Ожидает оценки преподавателя');await expect(answer).toBeDisabled();await page.reload();await page.locator('.taskbutton').filter({hasText:'Архив уровней'}).click();await expect(answer).toHaveValue(text.answer);await expect(answer).toBeDisabled();await expect(page.locator('.stage-intro')).toBeVisible();expect(sid).toBeTruthy();
});
