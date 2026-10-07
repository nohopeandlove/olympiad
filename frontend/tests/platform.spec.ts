import {test,expect,request} from '@playwright/test';
const URL='http://localhost:8080',PASSWORD='DevOnly!Python2026';
async function login(page:any,email:string){await page.goto('/login');await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Пароль',{exact:true}).fill(PASSWORD);await page.getByRole('button',{name:'Войти',exact:true}).click();await expect(page).toHaveURL(/dashboard/);}

test('Гость видит одно приключение и понятную регистрацию',async({page})=>{
 await page.goto('/');await expect(page.getByRole('heading',{level:1})).toHaveText('Сбой в Академии Алгоритмов');await expect(page.getByRole('link',{name:'Я школьник · 10–11 класс',exact:true})).toHaveCount(1);await expect(page.getByRole('link',{name:'Я студент СПО · 1–2 курс',exact:true})).toHaveCount(1);await expect(page.getByRole('combobox')).toHaveCount(0);await expect(page.getByText('Выбери свою олимпиаду',{exact:true})).toHaveCount(0);
 await page.getByText('Какие задания будут?',{exact:true}).click();await expect(page.locator('.simple-task-list li')).toHaveCount(8);await page.getByRole('button',{name:'Основной этап',exact:true}).click();await expect(page.locator('.simple-task-list li')).toHaveCount(10);
 await page.setViewportSize({width:390,height:844});await page.reload();expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);await page.screenshot({path:'/tmp/simple-adventure-mobile.png',fullPage:true});
});

test('Школьник видит только свои два этапа во всех разделах',async({page})=>{
 const faults:string[]=[];page.on('pageerror',e=>faults.push(e.message));
 const categories=await(await page.request.get('/api/olympiads')).json(),spo=categories.find((o:any)=>o.type==='SPO');
 await login(page,'school@example.org');await expect(page.getByText('Другие олимпиады',{exact:true})).toHaveCount(0);await expect(page.getByRole('heading',{name:'Отборочный этап',exact:true})).toHaveCount(1);await expect(page.getByRole('heading',{name:'Основной этап',exact:true})).toHaveCount(1);await expect(page.getByRole('link',{name:'Администратор',exact:true})).toHaveCount(0);
 await page.goto('/');await expect(page.locator('main')).toContainText('Школьники, 10–11 класс');await expect(page.getByRole('link',{name:/Я студент СПО/})).toHaveCount(0);await expect(page.getByRole('link',{name:'Открыть личный кабинет',exact:true})).toBeVisible();
 await page.goto('/schedule');await expect(page.locator('main')).toContainText('Школьники');await expect(page.locator('main')).not.toContainText('СПО');
 await page.goto('/results');await expect(page.locator('main')).not.toContainText('Студенты СПО');await expect(page.getByRole('combobox').locator('option')).toHaveText(['Все участники','10 класс','11 класс']);
 await page.goto('/register/'+spo.id);await expect(page.locator('.error')).toContainText('недоступна');await expect(page.getByRole('combobox',{name:'Курс',exact:true})).toHaveCount(0);expect((await page.request.get('/api/olympiads/'+spo.id)).status()).toBe(403);
 await page.goto('/dashboard');await expect(page.getByRole('heading',{name:'Отборочный этап',exact:true})).toBeVisible();await page.screenshot({path:'/tmp/simple-school-dashboard.png',fullPage:true});expect(faults).toEqual([]);
});

test('Студент СПО не видит школьную категорию',async({page})=>{
 await login(page,'spo1@example.org');await expect(page.getByRole('heading',{name:'Отборочный этап',exact:true})).toHaveCount(1);await expect(page.getByRole('heading',{name:'Основной этап',exact:true})).toHaveCount(1);await expect(page.getByText('Другие олимпиады',{exact:true})).toHaveCount(0);
 await page.goto('/');await expect(page.locator('main')).toContainText('Студенты СПО, 1–2 курс');await expect(page.getByRole('link',{name:/Я школьник/})).toHaveCount(0);await page.goto('/schedule');await expect(page.locator('main')).not.toContainText('Школьники');
 await page.goto('/results');await expect(page.getByRole('combobox').locator('option')).toHaveText(['Все участники','1 курс','2 курс']);
});

test('Администратор настраивает категории одного приключения без создания копий',async({page})=>{
 await login(page,'admin@example.org');await page.goto('/admin');await expect(page.getByRole('heading',{name:'Настройка приключения',exact:true})).toBeVisible();const category=page.getByRole('combobox',{name:'Категория участников',exact:true});await expect(category.locator('option')).toHaveText(['Школьники · 10–11 класс','Студенты СПО · 1–2 курс']);await expect(page.getByRole('button',{name:'Создать приключение',exact:true})).toHaveCount(0);await expect(page.getByRole('button',{name:'+ Создать олимпиаду',exact:true})).toHaveCount(0);
 await page.getByRole('button',{name:'Даты этапов',exact:true}).click();await expect(page.getByRole('button',{name:'Изменить',exact:true})).toHaveCount(2);await expect(page.getByRole('button',{name:'+ Добавить этап',exact:true})).toHaveCount(0);
 await page.getByRole('button',{name:'Задания',exact:true}).click();await expect(page.getByRole('button',{name:'Редактировать',exact:true})).toHaveCount(8);await page.getByRole('button',{name:'+ Добавить задание',exact:true}).click();const template=page.getByRole('combobox',{name:'Готовое задание',exact:true});await template.selectOption('q2');await page.getByRole('button',{name:'Заполнить задание',exact:true}).click();await expect(page.getByRole('combobox',{name:'Тип задания',exact:true})).toHaveValue('text');await expect(page.getByRole('textbox',{name:/^Критерии оценки/})).toHaveValue(/50 баллов/);await expect(page.getByRole('textbox',{name:/^Условие или вопрос/})).toHaveValue(/максимальный уровень/);
 await page.getByRole('combobox',{name:'Этап',exact:true}).selectOption({index:1});await expect(page.getByRole('button',{name:'Редактировать',exact:true})).toHaveCount(10);await expect(page.getByRole('heading',{name:'Последний протокол',exact:true})).toBeVisible();await expect(page.getByRole('heading',{name:'Журнал событий',exact:true})).toBeVisible();await page.screenshot({path:'/tmp/simple-admin.png',fullPage:true});await category.selectOption({label:'Студенты СПО · 1–2 курс'});await expect(page.getByRole('button',{name:'Редактировать',exact:true})).toHaveCount(8);await page.getByRole('button',{name:'+ Добавить задание',exact:true}).click();await template.selectOption('q2');await page.getByRole('button',{name:'Заполнить задание',exact:true}).click();await expect(page.getByRole('textbox',{name:/^Условие или вопрос/})).toHaveValue(/различный/);
});
