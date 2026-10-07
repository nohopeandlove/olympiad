import {test,expect,request} from '@playwright/test';
const URL='http://localhost:8080',PASSWORD='DevOnly!Python2026';
async function login(page:any,email:string){await page.goto('/login');await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Пароль',{exact:true}).fill(PASSWORD);await page.getByRole('button',{name:'Войти',exact:true}).click();await expect(page).toHaveURL(/dashboard/);}

test('Два этапа: вопросы, оценка преподавателя, часы и права меню',async({page,browser})=>{
 test.setTimeout(90000);
 const faults:string[]=[];page.on('pageerror',e=>faults.push(e.message));
 const admin=await request.newContext({baseURL:URL,extraHTTPHeaders:{Origin:URL}});
 const logged=await admin.post('/api/auth/login',{data:{email:'admin@example.org',password:PASSWORD}});expect(logged.status()).toBe(200);const csrf={'X-CSRF-Token':(await logged.json()).csrf};
 const now=Date.now(),event={type:'SCHOOL',title:'Mixed browser '+now,status:'active',registration_start:new Date(now-86400000).toISOString(),registration_end:new Date(now+86400000).toISOString(),ranking_visible:true};
 const created=await admin.post('/api/admin/olympiads',{headers:csrf,data:event});expect(created.status()).toBe(201);const oid=(await created.json()).id,feedback='Верное объяснение; добавьте случай отсутствия второго уровня. '+now;
 const reviewer=await browser.newContext();const review=await reviewer.newPage();
 try{
  const stage=await admin.post('/api/admin/olympiads/'+oid+'/stages',{headers:csrf,data:{title:'Побег из корпуса',story_intro:'Null закрыл дверь. Сначала восстановите пропуск.',kind:'qualifying',starts_at:new Date(now-60000).toISOString(),ends_at:new Date(now+86400000).toISOString(),duration_minutes:120}});expect(stage.status()).toBe(201);const sid=(await stage.json()).id;
  const later=await admin.post('/api/admin/olympiads/'+oid+'/stages',{headers:csrf,data:{title:'Доступ к ядру',story_intro:'Вы прошли тоннель. Теперь доберитесь до ядра.',kind:'main',starts_at:new Date(now+86400000).toISOString(),ends_at:new Date(now+172800000).toISOString(),duration_minutes:180}});expect(later.status()).toBe(201);
  const tasks=[{kind:'choice',position:1,title:'Панель двери',statement:'Выберите команду для чтения целого числа.',points:30,answer_options:['int(input())','input()'],correct_option:0},{kind:'text',position:2,title:'Отчёт ученика',statement:'Почему одинаковые уровни считаются один раз?',points:50,rubric:'Отличить повторения и различные значения.'}];
  for(const task of tasks)expect((await admin.post('/api/admin/stages/'+sid+'/tasks',{headers:csrf,data:task})).status()).toBe(201);
  await page.goto('/');await expect(page.getByRole('link',{name:'Администратор',exact:true})).toHaveCount(0);await expect(page.getByText('ГБПОУ «Челябинский радиотехнический техникум»',{exact:true}).first()).toBeVisible();
  await login(page,'school@example.org');await expect(page.getByRole('link',{name:'Администратор',exact:true})).toHaveCount(0);await expect(page.getByRole('link',{name:'Административная панель'})).toHaveCount(0);
  const profile=await(await page.request.get('/api/profile')).json();expect((await page.request.post('/api/registrations/'+oid,{headers:{Origin:URL,'X-CSRF-Token':profile.csrf},data:{school_class:11,consent_data:true,consent_rules:true}})).status()).toBe(201);
  await page.goto('/exam/'+sid);await page.bringToFront();await expect(page.locator('.stage-intro')).toContainText('Null закрыл дверь');await expect(page.locator('.monaco-editor')).toHaveCount(0);
  await page.getByRole('radio',{name:'int(input())',exact:true}).check();await expect(page.locator('.task-time')).toContainText('Идёт отсчёт');
  await expect(page.locator('.task-time')).not.toContainText('00:00:00',{timeout:5000});
  const focused=(await(await page.request.get('/api/stages/'+sid+'/task-times')).json()).timings[0];expect(focused.elapsed_ms).toBeGreaterThan(0);
  page.once('dialog',d=>d.accept());await page.getByRole('button',{name:'Отправить ответ',exact:true}).click();await expect(page.locator('.editorpanel .notice')).toContainText('Принято · 30 / 30');await expect(page.getByRole('button',{name:'Отправить ответ',exact:true})).toBeDisabled();
  await page.locator('.taskbutton').filter({hasText:'Отчёт ученика'}).click();const answer=page.getByRole('textbox',{name:'Развёрнутый ответ',exact:true});await answer.fill('Повторения не создают нового уровня: 9, 9, 7 → 7.');
  const saved=page.waitForResponse(r=>r.url().endsWith('/draft')&&r.request().method()==='PUT');await saved;await page.reload();await page.locator('.taskbutton').filter({hasText:'Отчёт ученика'}).click();await expect(answer).toHaveValue('Повторения не создают нового уровня: 9, 9, 7 → 7.');
  page.once('dialog',d=>d.accept());await page.getByRole('button',{name:'Отправить ответ',exact:true}).click();await expect(page.locator('.editorpanel .notice')).toContainText('Ожидает оценки преподавателя');await expect(answer).toBeDisabled();
  await page.screenshot({path:'/tmp/academy-mixed-exam.png',fullPage:true});
  await login(review,'admin@example.org');await review.goto('/admin');await review.locator('main > .row select').selectOption(oid);await review.getByRole('button',{name:'Решения',exact:true}).click();
  const textRow=review.locator('tbody tr').filter({hasText:'Отчёт ученика'});await textRow.getByRole('button',{name:'Открыть',exact:true}).click();await expect(review.getByText('Отличить повторения и различные значения.',{exact:true})).toBeVisible();
  await review.getByLabel('Баллы (0–50)',{exact:true}).fill('40');await review.getByLabel('Комментарий участнику').fill(feedback);await review.getByRole('button',{name:'Сохранить оценку',exact:true}).click();await expect(textRow).toContainText('40 / 50');
  await review.getByRole('button',{name:'Время по заданиям',exact:true}).click();await expect(review.locator('tbody')).toContainText('Панель двери');await expect(review.locator('tbody')).toContainText('Отчёт ученика');await review.screenshot({path:'/tmp/academy-admin-times.png',fullPage:true});
  await page.reload();await page.locator('.taskbutton').filter({hasText:'Отчёт ученика'}).click();await expect(page.locator('.editorpanel .notice')).toContainText('40 / 50');await expect(page.locator('.editorpanel .notice')).toContainText('Верное объяснение');
  await page.goto('/dashboard');const card=page.locator('section.card').filter({has:page.getByRole('heading',{name:event.title,exact:true})});await card.getByText('Моё время по заданиям',{exact:true}).click();await expect(card.locator('details')).toContainText('Панель двери:');await expect(card.locator('details')).toContainText('Отчёт ученика:');await expect(page.getByText(feedback,{exact:true})).toBeVisible();
  await review.goto('/dashboard');await review.getByRole('button',{name:'Выйти',exact:true}).click();await expect(review).toHaveURL(/login/);await expect(review.getByRole('link',{name:'Администратор',exact:true})).toHaveCount(0);
  await login(review,'school@example.org');await expect(review.getByRole('link',{name:'Администратор',exact:true})).toHaveCount(0);expect(faults).toEqual([]);
 }finally{await admin.put('/api/admin/olympiads/'+oid,{headers:csrf,data:{...event,status:'draft'}});await reviewer.close();await admin.dispose();}
});

test('Администратор создаёт оба вида вопроса из шаблонов отборочного этапа',async({page})=>{
 const admin=await request.newContext({baseURL:URL,extraHTTPHeaders:{Origin:URL}});const loginResult=await admin.post('/api/auth/login',{data:{email:'admin@example.org',password:PASSWORD}});expect(loginResult.status()).toBe(200);const csrf={'X-CSRF-Token':(await loginResult.json()).csrf},now=Date.now();
 const event=await admin.post('/api/admin/olympiads',{headers:csrf,data:{type:'SCHOOL',title:'Question form '+now,status:'draft',registration_start:new Date(now).toISOString(),registration_end:new Date(now+86400000).toISOString()}});expect(event.status()).toBe(201);const oid=(await event.json()).id;
 const stage=await admin.post('/api/admin/olympiads/'+oid+'/stages',{headers:csrf,data:{title:'Отборочный',kind:'qualifying',starts_at:new Date(now+86400000).toISOString(),ends_at:new Date(now+172800000).toISOString(),duration_minutes:120}});expect(stage.status()).toBe(201);const sid=(await stage.json()).id;
 try{
  await login(page,'admin@example.org');await page.goto('/admin');await page.locator('main > .row select').selectOption(oid);await page.getByRole('button',{name:'Задания',exact:true}).click();await page.getByRole('button',{name:'+ Добавить задание',exact:true}).click();
  const templates=page.getByRole('combobox',{name:'Глава приключения',exact:true});await expect(templates.locator('option')).toHaveCount(8);await templates.selectOption('q1');await page.getByRole('button',{name:'Использовать выбранную главу',exact:true}).click();await expect(page.getByRole('combobox',{name:'Тип задания',exact:true})).toHaveValue('choice');await expect(page.getByLabel('Вариант 1',{exact:true})).toHaveValue('n = int(input())');
  await page.getByRole('button',{name:'Сохранить задание',exact:true}).click();await expect(page.getByRole('heading',{name:'Диагностика панели',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'+ Добавить задание',exact:true}).click();await templates.selectOption('q2');await page.getByRole('button',{name:'Использовать выбранную главу',exact:true}).click();await expect(page.getByRole('combobox',{name:'Тип задания',exact:true})).toHaveValue('text');await expect(page.getByRole('textbox',{name:/^Критерии оценки/})).toHaveValue(/50 баллов/);await page.getByRole('button',{name:'Сохранить задание',exact:true}).click();await expect(page.getByRole('heading',{name:'Архив уровней',exact:true})).toBeVisible();
  const rows=await(await admin.get('/api/admin/stages/'+sid+'/tasks')).json();expect(rows.map((t:any)=>t.kind)).toEqual(['choice','text']);expect(rows[0].correct_option).toBe(0);expect(rows[0].tests).toEqual([]);expect(rows[1].rubric).toContain('50 баллов');expect(rows[1].tests).toEqual([]);await page.screenshot({path:'/tmp/academy-question-admin.png',fullPage:true});
 }finally{await admin.dispose();}
});
