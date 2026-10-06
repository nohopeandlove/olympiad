import {test,expect,request} from '@playwright/test';
const PASSWORD='DevOnly!Python2026';
async function login(page:any,email:string){
 if(email!=='admin@example.org'){
  const admin=await request.newContext({baseURL:'http://localhost:8080',extraHTTPHeaders:{Origin:'http://localhost:8080'}});
  const login=await admin.post('/api/auth/login',{data:{email:'admin@example.org',password:PASSWORD}});expect(login.status()).toBe(200);const auth=await login.json();
  const os=await (await admin.get('/api/admin/olympiads')).json();
  for(const o of os){const rows=await (await admin.get('/api/admin/olympiads/'+o.id+'/participants?q='+encodeURIComponent(email))).json();const stages=await(await admin.get('/api/admin/olympiads/'+o.id+'/stages')).json();for(const r of rows)for(const s of stages)await admin.post('/api/admin/participants/'+r.id+'/reset-session/'+s.id,{headers:{'X-CSRF-Token':auth.csrf}});}
  await admin.dispose();
 }
await page.goto('/login');await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Пароль',{exact:true}).fill(PASSWORD);await page.getByRole('button',{name:'Войти',exact:true}).click();await expect(page).toHaveURL(/dashboard/);}
test('Главная и отдельные регистрационные формы',async({page})=>{
 await page.goto('/');await expect(page.getByRole('heading',{name:'Выбери свою олимпиаду'})).toBeVisible();
 const cards=page.locator('article');await expect(cards).toHaveCount(2);
 await cards.filter({hasText:'Для школьников'}).getByRole('link',{name:/Зарегистрироваться/}).click();
 await expect(page.getByRole('combobox',{name:'Класс',exact:true})).toBeVisible();await expect(page.getByRole('combobox',{name:'Курс',exact:true})).toHaveCount(0);await expect(page.getByText(/наставник/i)).toHaveCount(0);
 await page.goto('/');await page.locator('article').filter({hasText:'1 и 2 курс СПО'}).getByRole('link',{name:/Зарегистрироваться/}).click();
 await expect(page.getByRole('combobox',{name:'Курс',exact:true})).toBeVisible();await expect(page.getByRole('combobox',{name:'Класс',exact:true})).toHaveCount(0);await expect(page.getByText(/наставник/i)).toHaveCount(0);
});
test('Администратор видит отдельные олимпиады, этапы и скрытые тесты',async({page})=>{
 await login(page,'admin@example.org');await page.goto('/admin');
 await expect(page.getByRole('heading',{name:'Администрирование'})).toBeVisible();
 await page.locator('main > .row select').selectOption({label:'Школьники · Олимпиада для школьников'});
 await page.getByRole('button',{name:'Настройки',exact:true}).click();await expect(page.getByLabel('Начало регистрации')).toBeVisible();
 await page.getByRole('button',{name:'Этапы',exact:true}).click();await expect(page.getByRole('heading',{name:'Отборочный этап'})).toBeVisible();
 await page.getByRole('button',{name:'Задания',exact:true}).click();await page.getByRole('button',{name:'Редактировать',exact:true}).first().click();await expect(page.getByRole('heading',{name:'Примеры проверки',exact:true})).toBeVisible();await expect(page.getByLabel('Публичный пример')).toHaveCount(2);
});
test('Monaco, отправка, восстановление черновика и разделение задач',async({page})=>{
 const faults:string[]=[];page.on('pageerror',e=>faults.push(e.message));
 await login(page,'school@example.org');await page.getByRole('button',{name:/Начать этап|Продолжить этап/}).first().click();
 await expect(page.locator('.monaco-editor')).toBeVisible({timeout:20000});
 await expect(page.locator('.statement h2')).toHaveText('Сумма двух чисел');
 await expect(page.getByText('Сумма квадратов',{exact:true})).toHaveCount(0);
 await page.locator('.monaco-editor textarea').focus();await page.keyboard.press('Control+A');await page.keyboard.type('print(sum(map(int,input().split())))');
 await expect(page.getByText('Черновик сохранён на сервере',{exact:true})).toBeVisible({timeout:15000});
 await page.getByRole('button',{name:'Отправить решение',exact:true}).click();await expect(page.locator('.console')).toContainText('Accepted',{timeout:30000});
 await expect(page.locator('.timer')).not.toHaveText('00:00:00');const before=await page.locator('.timer').textContent();await page.reload();await expect(page.locator('.monaco-editor')).toBeVisible();await expect(page.locator('.monaco-editor')).toContainText('sum');
 await expect(page.locator('.timer')).not.toHaveText('00:00:00');const after=await page.locator('.timer').textContent();const seconds=(s:string|null)=>s!.split(':').reduce((n,v)=>n*60+Number(v),0);expect(seconds(after)).toBeGreaterThan(0);expect(seconds(after)).toBeLessThanOrEqual(seconds(before));expect(faults).toEqual([]);
 await page.screenshot({path:'/tmp/olympiad-exam.png',fullPage:true});
});
test('Участник СПО получает только задачи СПО',async({page})=>{
 await login(page,'spo1@example.org');await page.getByRole('button',{name:/Начать этап|Продолжить этап/}).first().click();
 await expect(page.locator('.statement h2')).toHaveText('Сумма квадратов');await expect(page.getByText('Сумма двух чисел',{exact:true})).toHaveCount(0);
});

test('Упрощённая форма: пример, предпросмотр и сохранение',async({page})=>{
 await login(page,'admin@example.org');await page.goto('/admin');
 await page.locator('main > .row select').selectOption({label:'Школьники · Олимпиада для школьников'});
 await page.getByRole('button',{name:'Задания',exact:true}).click();
 await page.getByRole('button',{name:'+ Добавить задание',exact:true}).click();
 await page.getByRole('button',{name:'Заполнить учебным примером',exact:true}).click();
 await expect(page.getByLabel('Название',{exact:true})).toHaveValue('Сумма двух чисел');
 await page.getByRole('button',{name:'Посмотреть условие глазами участника'}).click();
 await expect(page.locator('form').getByRole('heading',{name:'Сумма двух чисел',exact:true})).toBeVisible();
 let payload:any;
 await page.route('**/api/admin/stages/*/tasks',async route=>{if(route.request().method()==='POST'){payload=route.request().postDataJSON();await route.fulfill({status:201,json:{id:'test-task'}});}else await route.continue();});
 await page.getByRole('button',{name:'Сохранить задание',exact:true}).click();
 await expect(page.getByText('Изменения сохранены',{exact:true})).toBeVisible();
 expect(payload.time_limit).toBe(2);expect(payload.memory_limit).toBe(128);
 expect(payload.tests).toEqual([{input:'2 3\n',expected:'5\n',public:true},{input:'-10 7\n',expected:'-3\n',public:false}]);
});

test('Космические шаблоны: пустой ввод, скрытые проверки и замена',async({page})=>{
 await login(page,'admin@example.org');await page.goto('/admin');
 await page.locator('main > .row select').selectOption({label:'Школьники · Олимпиада для школьников'});
 await page.getByRole('button',{name:'Задания',exact:true}).click();await page.getByRole('button',{name:'+ Добавить задание',exact:true}).click();
 const templates=page.getByRole('combobox',{name:'Готовая задача',exact:true});await expect(templates.locator('option')).toHaveCount(19);
 await page.getByRole('button',{name:'Использовать выбранную задачу'}).click();
 await expect(page.getByLabel('Название',{exact:true})).toHaveValue('Тайное послание звёзд');
 await expect(page.getByLabel('Вход',{exact:true})).toHaveValue('');
 await expect(page.getByRole('textbox',{name:'Ожидаемый вывод',exact:true})).toHaveValue('Я звёздный путешественник!');
 await templates.selectOption('20');page.once('dialog',dialog=>dialog.dismiss());await page.getByRole('button',{name:'Использовать выбранную задачу'}).click();
 await expect(page.getByLabel('Название',{exact:true})).toHaveValue('Тайное послание звёзд');
 page.once('dialog',dialog=>dialog.accept());await page.getByRole('button',{name:'Использовать выбранную задачу'}).click();
 await expect(page.getByLabel('Название',{exact:true})).toHaveValue('Секреты звёздного рейтинга');
 let payload:any;await page.route('**/api/admin/stages/*/tasks',async route=>{if(route.request().method()==='POST'){payload=route.request().postDataJSON();await route.fulfill({status:201,json:{id:'test-task'}});}else await route.continue();});
 await page.getByRole('button',{name:'Сохранить задание',exact:true}).click();await expect(page.getByText('Изменения сохранены',{exact:true})).toBeVisible();
 expect(payload.tests).toHaveLength(5);expect(payload.tests.filter((t:any)=>t.public)).toHaveLength(2);
 expect(payload.tests).toContainEqual({input:'Луна',expected:'15',public:false});expect(payload.constraints).toContain('словарь');
});
