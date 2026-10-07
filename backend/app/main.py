from typing import Literal
import csv, io, secrets, smtplib
from datetime import timedelta
from email.message import EmailMessage
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from sqlalchemy import select, func, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DBSession
from .db import get_db
from .models import *
from .schemas import *
from .security import current_user, admin, limit, hasher, password_ok, dummy_hash, digest, new_session, exam_session
from .config import settings
from .academy import category_pack, PACK, create_academy, academy_id, ordered_tasks, completed_chapters
from .task_timing import checkpoint, snapshot

app = FastAPI(title='Python Олимпиады', version='1.0.0', docs_url='/api/docs', openapi_url='/api/openapi.json')

@app.middleware('http')
async def headers(request, call_next):
    response = await call_next(request)
    response.headers.update({'X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY','Referrer-Policy':'same-origin','Cache-Control':'no-store'})
    return response

def get_or_404(db, model, id):
    row = db.get(model,id)
    if not row: raise HTTPException(404,'Не найдено')
    return row

def serialize(row, exclude=()):
    return {c.key:getattr(row,c.key) for c in row.__mapper__.column_attrs if c.key not in exclude}

def user_data(user): return serialize(user,('password_hash',))
def audit(db,user,action,id): db.add(AuditLog(actor_id=user.id,action=action,target_id=id))

def registration(db,user,oid):
    row=db.scalar(select(Registration).where(Registration.user_id==user.id,Registration.olympiad_id==oid))
    if not row or row.status!='registered': raise HTTPException(403,'Нет действующей регистрации на эту олимпиаду')
    if not user.verified: raise HTTPException(403,'Подтвердите email')
    o=db.get(Olympiad,oid)
    if o.type=='SCHOOL' and row.school_class not in (10,11): raise HTTPException(403,'Участие доступно только школьникам 10 и 11 классов')
    return row

def valid_registration(o,data):
    if o.status not in ('scheduled','active') or not o.registration_start <= now() < o.registration_end: raise HTTPException(403,'Регистрация закрыта')
    if o.type=='SCHOOL' and (data.school_class not in (10,11) or data.school_class not in o.allowed_classes or data.course is not None or data.group): raise HTTPException(422,'Для школьников доступны только 10 и 11 классы; курс и группа не допускаются')
    if o.type=='SPO' and (data.course not in (1,2) or data.school_class is not None): raise HTTPException(422,'Для СПО допустим только 1 или 2 курс')
    if not data.consent_data or not data.consent_rules: raise HTTPException(422,'Необходимо согласие')

def active_attempt(db,user,stage,request=None):
    r=registration(db,user,stage.olympiad_id)
    o=get_or_404(db,Olympiad,stage.olympiad_id)
    a=db.scalar(select(Attempt).where(Attempt.registration_id==r.id,Attempt.stage_id==stage.id))
    if o.status!='active' or not stage.starts_at <= now() < stage.ends_at or not a or a.finished or now()>=a.deadline: raise HTTPException(403,'Этап не активен или время истекло')
    if request and a.session_hash!=exam_session(request): raise HTTPException(409,'Этап открыт в другой сессии')
    return a

@app.get('/api/health')
def health(db: DBSession=Depends(get_db)):
    db.execute(select(1))
    return {'status':'ok','server_time':now()}

def public_stages(db, oid):
    result=[]
    for stage in db.scalars(select(Stage).where(Stage.olympiad_id==oid).order_by(Stage.starts_at)):
        chapters=[{'id':t.id,'title':t.title,'points':t.points,'difficulty':t.difficulty,'academy_chapter':t.academy_chapter,'kind':t.kind} for t in ordered_tasks(db.scalars(select(Task).where(Task.stage_id==stage.id,Task.olympiad_id==oid)))]
        result.append(serialize(stage)|{'chapters':chapters})
    return result

def browsing_user(request,db):
    session=db.get(Session,digest(request.cookies.get('session',''))) if request.cookies.get('session') else None
    if not session or session.expires_at<=now():return None
    user=db.get(User,session.user_id)
    if user and user.blocked:raise HTTPException(403,'Аккаунт заблокирован')
    return user

def participant_category(db,user):
    if not user or user.role=='admin':return None
    return db.scalar(select(Olympiad.type).join(Registration,Registration.olympiad_id==Olympiad.id).where(Registration.user_id==user.id).order_by(Registration.consent_at,Registration.id).limit(1))

def visible_event(db,event,user):
    if user and user.role=='admin':return
    if event.id not in {academy_id('SCHOOL'),academy_id('SPO')} or event.status=='draft':raise HTTPException(404,'Олимпиада не найдена')
    category=participant_category(db,user)
    if category and event.type!=category:raise HTTPException(403,'Эта категория участия вам недоступна')

@app.get('/api/olympiads')
def olympiads(request:Request,db: DBSession=Depends(get_db)):
    user=browsing_user(request,db);category=participant_category(db,user)
    query=select(Olympiad).where(Olympiad.id.in_([academy_id('SCHOOL'),academy_id('SPO')]),Olympiad.status!='draft').order_by(Olympiad.type)
    if category:query=query.where(Olympiad.type==category)
    return [serialize(o)|{'stages':public_stages(db,o.id)} for o in db.scalars(query)]

@app.get('/api/olympiads/{oid}')
def olympiad(oid:str,request:Request,db:DBSession=Depends(get_db)):
    o=get_or_404(db,Olympiad,oid);visible_event(db,o,browsing_user(request,db))
    return serialize(o)|{'stages':public_stages(db,oid)}

@app.post('/api/auth/register',status_code=201)
def register(data:Register,request:Request,db:DBSession=Depends(get_db)):
    if request.headers.get('origin')!=settings.public_origin: raise HTTPException(403,'Недопустимый Origin')
    limit('register:'+request.headers.get('x-real-ip',request.client.host),10,3600)
    o=get_or_404(db,Olympiad,data.olympiad_id); valid_registration(o,data)
    u=User(**data.model_dump(exclude={'olympiad_id','password','confirm_password','school_class','course','group','consent_data','consent_rules'}),password_hash=hasher.hash(data.password))
    u.email=str(data.email).lower()
    db.add(u)
    try:
        db.flush()
        db.add(Registration(user_id=u.id,olympiad_id=o.id,school_class=data.school_class,course=data.course,group=data.group))
        token=secrets.token_urlsafe(32)
        db.add(Verification(id=digest(token),user_id=u.id,expires_at=now()+timedelta(hours=24)))
        if not settings.smtp_host: raise HTTPException(503,'Почтовый сервис не настроен')
        message=EmailMessage(); message['From']=settings.smtp_from; message['To']=u.email; message['Subject']='Подтверждение email — Python Олимпиады'
        message.set_content(f'Подтвердите email: {settings.public_origin}/verify?token={token}')
        with smtplib.SMTP(settings.smtp_host,settings.smtp_port,timeout=10) as smtp:
            if settings.smtp_starttls: smtp.starttls()
            if settings.smtp_user: smtp.login(settings.smtp_user,settings.smtp_password)
            smtp.send_message(message)
        db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409,'Email уже зарегистрирован')
    except (OSError,smtplib.SMTPException):
        db.rollback(); raise HTTPException(503,'Не удалось отправить письмо')
    return {'message':'Проверьте почту для подтверждения email'}

@app.post('/api/auth/verify')
def verify(token:str,db:DBSession=Depends(get_db)):
    v=db.get(Verification,digest(token))
    if not v or v.expires_at<now(): raise HTTPException(400,'Ссылка недействительна')
    db.get(User,v.user_id).verified=True; db.delete(v); db.commit()
    return {'message':'Email подтверждён'}

@app.post('/api/auth/login')
def login(data:Login,request:Request,response:Response,db:DBSession=Depends(get_db)):
    if request.headers.get('origin')!=settings.public_origin: raise HTTPException(403,'Недопустимый Origin')
    limit('login:ip:'+request.headers.get('x-real-ip',request.client.host),30,900); limit('login:email:'+digest(str(data.email).lower()),10,900)
    u=db.scalar(select(User).where(User.email==str(data.email).lower()))
    valid=password_ok(data.password,u.password_hash if u else dummy_hash)
    if not u or not valid: raise HTTPException(401,'Неверный email или пароль')
    if u.blocked or not u.verified: raise HTTPException(403,'Аккаунт заблокирован или email не подтверждён')
    return {'user':user_data(u),'csrf':new_session(db,u,response)}

@app.post('/api/auth/logout')
def logout(request:Request,response:Response,u:User=Depends(current_user),db:DBSession=Depends(get_db)):
    db.delete(request.state.session); db.commit(); response.delete_cookie('session')
    return {'message':'Вы вышли'}

@app.get('/api/profile')
def profile(request:Request,u:User=Depends(current_user),db:DBSession=Depends(get_db)):
    regs=[]
    category=participant_category(db,u)
    query=select(Registration).where(Registration.user_id==u.id)
    query=query.where(Registration.olympiad_id.in_([academy_id('SCHOOL'),academy_id('SPO')]))
    if category:query=query.where(Registration.olympiad_id==academy_id(category))
    for r in db.scalars(query):
        regs.append(serialize(r)|{'olympiad':serialize(db.get(Olympiad,r.olympiad_id)),'stages':[serialize(s)|{'academy_ending_unlocked':8 in completed_chapters(db,u.id,s.id)} for s in db.scalars(select(Stage).where(Stage.olympiad_id==r.olympiad_id))],'attempts':[serialize(a,('session_hash',)) for a in db.scalars(select(Attempt).where(Attempt.registration_id==r.id))]})
    return {'user':user_data(u),'category':category,'csrf':request.state.session.csrf,'registrations':regs,'notifications':[serialize(n) for n in db.scalars(select(Notification).where(Notification.user_id==u.id))],'submissions':[serialize(s,('code',)) for s in db.scalars(select(Submission).where(Submission.user_id==u.id,Submission.olympiad_id.in_([r['olympiad_id'] for r in regs])).order_by(Submission.created_at.desc()).limit(100))],'server_time':now()}

@app.post('/api/registrations/{oid}',status_code=201)
def join(oid:str,data:Join,u:User=Depends(current_user),db:DBSession=Depends(get_db)):
    o=get_or_404(db,Olympiad,oid); valid_registration(o,data)
    if u.role!='admin':
        categories=set(db.scalars(select(Olympiad.type).join(Registration,Registration.olympiad_id==Olympiad.id).where(Registration.user_id==u.id)))
        if categories and o.type not in categories: raise HTTPException(403,'Аккаунт зарегистрирован в другой образовательной категории')
    r=Registration(user_id=u.id,olympiad_id=oid,school_class=data.school_class,course=data.course,group=data.group); db.add(r)
    try: db.commit()
    except IntegrityError: db.rollback(); raise HTTPException(409,'Вы уже зарегистрированы')
    return serialize(r)

@app.post('/api/stages/{sid}/start')
def start(sid:str,request:Request,u:User=Depends(current_user),db:DBSession=Depends(get_db)):
    s=get_or_404(db,Stage,sid); r=registration(db,u,s.olympiad_id); o=db.get(Olympiad,s.olympiad_id)
    if o.status!='active' or not s.starts_at<=now()<s.ends_at: raise HTTPException(403,'Этап ещё не начался или завершён')
    a=db.scalar(select(Attempt).where(Attempt.registration_id==r.id,Attempt.stage_id==sid))
    if a and not a.session_hash:
        a.session_hash=exam_session(request); db.commit()
    if a and a.session_hash!=exam_session(request):
        db.add(AntiCheatEvent(participant_id=r.id,olympiad_id=s.olympiad_id,stage_id=sid,event_type='OTHER',metadata_json={'reason':'SECOND_SESSION'},severity='warning')); db.commit()
        raise HTTPException(409,'Этап уже открыт в другой сессии; обратитесь к администратору')
    if not a:
        a=Attempt(registration_id=r.id,stage_id=sid,deadline=min(now()+timedelta(minutes=s.duration_minutes),s.ends_at),session_hash=exam_session(request)); db.add(a)
        try: db.commit()
        except IntegrityError: db.rollback(); raise HTTPException(409,'Этап уже начат; обновите страницу')
    return serialize(a,('session_hash',))|{'server_time':now()}

@app.post('/api/stages/{sid}/finish')
def finish(sid:str,request:Request,u:User=Depends(current_user),db:DBSession=Depends(get_db)):
    stage=get_or_404(db,Stage,sid); a=active_attempt(db,u,stage,request)
    a=db.scalar(select(Attempt).where(Attempt.id==a.id).with_for_update().execution_options(populate_existing=True))
    checkpoint(db,a,stage);a.active_task_id=None;a.finished=True;db.commit();return {'message':'Этап завершён'}

@app.get('/api/stages/{sid}/tasks')
def tasks(sid:str,request:Request,u:User=Depends(current_user),db:DBSession=Depends(get_db)):
    s=get_or_404(db,Stage,sid); active_attempt(db,u,s,request)
    result=[]
    for t in ordered_tasks(db.scalars(select(Task).where(Task.stage_id==sid,Task.olympiad_id==s.olympiad_id))):
        submitted=db.scalar(select(Submission).where(Submission.task_id==t.id,Submission.user_id==u.id,Submission.mode=='submit').order_by(Submission.created_at.desc()).limit(1))
        result.append(serialize(t,('correct_option','rubric'))|{'examples':[serialize(c,('task_id',)) for c in db.scalars(select(TestCase).where(TestCase.task_id==t.id,TestCase.public==True))],'my_submission':serialize(submitted) if submitted else None})
    return result

@app.post('/api/stages/{sid}/task-focus')
def task_focus(sid:str,data:TaskFocusInput,request:Request,u:User=Depends(current_user),db:DBSession=Depends(get_db)):
    stage=get_or_404(db,Stage,sid);a=active_attempt(db,u,stage,request);limit('timing:'+u.id,60,60)
    if data.task_id:
        task=get_or_404(db,Task,data.task_id)
        if task.stage_id!=sid or task.olympiad_id!=stage.olympiad_id:raise HTTPException(403,'Задание относится к другому этапу')
    a=db.scalar(select(Attempt).where(Attempt.id==a.id).with_for_update().execution_options(populate_existing=True))
    if a.finished or now()>=a.deadline or a.session_hash!=exam_session(request):raise HTTPException(409,'Сессия этапа изменилась')
    timestamp=now();checkpoint(db,a,stage,timestamp);a.active_task_id=data.task_id
    if data.task_id and not db.scalar(select(TaskTime).where(TaskTime.attempt_id==a.id,TaskTime.task_id==data.task_id)):
        db.add(TaskTime(attempt_id=a.id,task_id=data.task_id,elapsed_ms=0,first_opened_at=timestamp))
    db.commit();return snapshot(db,a,stage,timestamp)

@app.get('/api/stages/{sid}/task-times')
def task_times(sid:str,u:User=Depends(current_user),db:DBSession=Depends(get_db)):
    stage=get_or_404(db,Stage,sid);reg=registration(db,u,stage.olympiad_id)
    attempt=db.scalar(select(Attempt).where(Attempt.registration_id==reg.id,Attempt.stage_id==sid))
    result=snapshot(db,attempt,stage) if attempt else {'timings':[],'server_time':now()}
    for row in result['timings']:row['task_title']=db.get(Task,row['task_id']).title
    return result

@app.get('/api/stages/{sid}/academy-ending')
def academy_ending(sid:str,u:User=Depends(current_user),db:DBSession=Depends(get_db)):
    stage=get_or_404(db,Stage,sid); registration(db,u,stage.olympiad_id)
    if 8 not in completed_chapters(db,u.id,sid): raise HTTPException(403,'Финал откроется после решения «Последнего протокола»')
    return {'title':'Ядро восстановлено. Но кто такой Null?', 'text':PACK['finale']}

@app.get('/api/stages/{sid}/academy-progress')
def academy_progress(sid:str,u:User=Depends(current_user),db:DBSession=Depends(get_db)):
    stage=get_or_404(db,Stage,sid); registration(db,u,stage.olympiad_id)
    chapters=completed_chapters(db,u.id,sid)
    return {'completed_chapters':chapters,'ending_unlocked':8 in chapters}

@app.get('/api/tasks/{tid}/draft')
def get_draft(tid:str,request:Request,u:User=Depends(current_user),db:DBSession=Depends(get_db)):
    t=get_or_404(db,Task,tid); active_attempt(db,u,db.get(Stage,t.stage_id),request)
    d=db.scalar(select(Draft).where(Draft.user_id==u.id,Draft.task_id==tid)); return {'code':d.code if d else ''}

@app.put('/api/tasks/{tid}/draft')
def save_draft(tid:str,data:DraftInput,request:Request,u:User=Depends(current_user),db:DBSession=Depends(get_db)):
    t=get_or_404(db,Task,tid); active_attempt(db,u,db.get(Stage,t.stage_id),request); limit('draft:'+u.id,120,60)
    d=db.scalar(select(Draft).where(Draft.user_id==u.id,Draft.task_id==tid))
    if not d: d=Draft(user_id=u.id,task_id=tid); db.add(d)
    d.code=data.code; db.commit(); return {'saved':True}

@app.post('/api/tasks/{tid}/submissions',status_code=202)
def submit(tid:str,data:CodeInput,request:Request,u:User=Depends(current_user),db:DBSession=Depends(get_db)):
    t=get_or_404(db,Task,tid); a=active_attempt(db,u,db.get(Stage,t.stage_id),request); limit('submit:'+u.id,20,60)
    a=db.scalar(select(Attempt).where(Attempt.id==a.id).with_for_update().execution_options(populate_existing=True))
    if a.finished or now()>=a.deadline or a.session_hash!=exam_session(request):raise HTTPException(409,'Сессия этапа изменилась')
    if t.kind!='code':raise HTTPException(422,'Для контрольного вопроса используйте отправку ответа')
    s=Submission(user_id=u.id,olympiad_id=t.olympiad_id,stage_id=t.stage_id,task_id=tid,code=data.code,mode=data.mode); db.add(s); db.commit()
    from .jobs import judge_submission
    try: judge_submission.delay(s.id)
    except Exception:
        s.status='System Error'; db.commit(); raise HTTPException(503,'Очередь недоступна')
    return serialize(s,('code',))

@app.post('/api/tasks/{tid}/answers',status_code=201)
def answer(tid:str,data:AnswerInput,request:Request,u:User=Depends(current_user),db:DBSession=Depends(get_db)):
    t=get_or_404(db,Task,tid);a=active_attempt(db,u,db.get(Stage,t.stage_id),request);limit('submit:'+u.id,20,60)
    a=db.scalar(select(Attempt).where(Attempt.id==a.id).with_for_update().execution_options(populate_existing=True))
    if a.finished or now()>=a.deadline or a.session_hash!=exam_session(request):raise HTTPException(409,'Сессия этапа изменилась')
    if t.kind=='code':raise HTTPException(422,'Для задачи на Python отправьте программу')
    if db.scalar(select(Submission.id).where(Submission.user_id==u.id,Submission.task_id==tid,Submission.mode=='submit').limit(1)):raise HTTPException(409,'Ответ уже отправлен; повторная отправка недоступна')
    if t.kind=='choice':
        if data.answer or data.option_index is None or data.option_index>=len(t.answer_options):raise HTTPException(422,'Выберите один вариант ответа')
        correct=data.option_index==t.correct_option
        s=Submission(user_id=u.id,olympiad_id=t.olympiad_id,stage_id=t.stage_id,task_id=tid,code=str(data.option_index),status='Accepted' if correct else 'Wrong Answer',score=t.points if correct else 0)
    else:
        if not data.answer.strip() or data.option_index is not None:raise HTTPException(422,'Введите развёрнутый ответ')
        s=Submission(user_id=u.id,olympiad_id=t.olympiad_id,stage_id=t.stage_id,task_id=tid,code=data.answer,status='Pending Review')
    db.add(s);db.flush();db.add(SubmissionResult(submission_id=s.id,detail={'message':'Ответ сохранён. Ожидает оценки преподавателя.' if t.kind=='text' else 'Ответ проверен.'}));db.commit()
    return serialize(s)

@app.post('/api/admin/submissions/{id}/review')
def review_answer(id:str,data:ReviewInput,u:User=Depends(admin),db:DBSession=Depends(get_db)):
    s=get_or_404(db,Submission,id);t=db.get(Task,s.task_id)
    if t.kind!='text' or s.mode!='submit':raise HTTPException(422,'Ручная оценка доступна только для развёрнутого ответа')
    if data.score>t.points:raise HTTPException(422,'Оценка превышает максимум за задание')
    s.score=data.score;s.status='Accepted' if data.score==t.points else 'Reviewed';s.review_feedback=data.feedback;s.reviewed_by=u.id;s.reviewed_at=now()
    result=db.scalar(select(SubmissionResult).where(SubmissionResult.submission_id==id))
    if result:result.detail={'feedback':data.feedback}
    audit(db,u,'REVIEW_ANSWER',id);db.add(Notification(user_id=s.user_id,message=f'Ответ «{t.title}» оценён: {data.score} / {t.points}. {data.feedback}'));db.commit();return serialize(s)

@app.get('/api/submissions/{id}')
def submission(id:str,u:User=Depends(current_user),db:DBSession=Depends(get_db)):
    s=get_or_404(db,Submission,id)
    if s.user_id!=u.id and u.role!='admin': raise HTTPException(403,'Нет доступа')
    r=db.scalar(select(SubmissionResult).where(SubmissionResult.submission_id==id))
    t=db.get(Task,s.task_id)
    return serialize(s)|{'result':r.detail if r else None,'task':serialize(t) if u.role=='admin' else {'title':t.title,'kind':t.kind,'points':t.points}}

@app.post('/api/anti-cheat/{sid}')
def event(sid:str,data:EventInput,request:Request,u:User=Depends(current_user),db:DBSession=Depends(get_db)):
    s=get_or_404(db,Stage,sid); r=registration(db,u,s.olympiad_id); active_attempt(db,u,s,request); limit('events:'+u.id,120,60)
    if any(len(v)>200 for v in data.metadata.values()): raise HTTPException(422,'Слишком длинные метаданные')
    db.add(AntiCheatEvent(participant_id=r.id,olympiad_id=s.olympiad_id,stage_id=sid,event_type=data.event_type,metadata_json=data.metadata)); db.commit(); return {'saved':True}

@app.get('/api/results/{oid}')
def results(oid:str,request:Request,level:int|None=None,db:DBSession=Depends(get_db)):
    o=get_or_404(db,Olympiad,oid);visible_event(db,o,browsing_user(request,db))
    if not o.ranking_visible: raise HTTPException(403,'Рейтинг пока скрыт')
    return ranking(db,oid,level)

def ranking(db,oid,level=None):
    o=db.get(Olympiad,oid); rows=[]
    for r in db.scalars(select(Registration).where(Registration.olympiad_id==oid,Registration.status=='registered')):
        if level is not None and (r.school_class if o.type=='SCHOOL' else r.course)!=level: continue
        u=db.get(User,r.user_id)
        if u.blocked: continue
        scores=db.execute(select(Submission.task_id,func.max(Submission.score)).where(Submission.user_id==u.id,Submission.olympiad_id==oid,Submission.mode=='submit').group_by(Submission.task_id)).all()
        rows.append({'participant_id':r.id,'name':f'{u.last_name} {u.first_name}','school_class':r.school_class,'course':r.course,'score':sum(x[1] for x in scores)})
    rows.sort(key=lambda r:(-r['score'],r['name'],r['participant_id']))
    return [r|{'place':i+1} for i,r in enumerate(rows)]

@app.get('/api/admin/olympiads')
def admin_olympiads(current:bool=False,u:User=Depends(admin),db:DBSession=Depends(get_db)):
    query=select(Olympiad).order_by(Olympiad.type,Olympiad.title)
    if current:query=query.where(Olympiad.id.in_([academy_id('SCHOOL'),academy_id('SPO')]))
    return [serialize(o) for o in db.scalars(query)]

@app.post('/api/admin/olympiads',status_code=201)
def create_olympiad(data:OlympiadInput,u:User=Depends(admin),db:DBSession=Depends(get_db)):
    o=Olympiad(**data.model_dump()); db.add(o); db.flush(); audit(db,u,'CREATE_OLYMPIAD',o.id); db.commit(); return serialize(o)

@app.put('/api/admin/olympiads/{oid}')
def update_olympiad(oid:str,data:OlympiadInput,u:User=Depends(admin),db:DBSession=Depends(get_db)):
    o=get_or_404(db,Olympiad,oid)
    if o.type!=data.type and db.scalar(select(func.count()).select_from(Registration).where(Registration.olympiad_id==oid)): raise HTTPException(409,'Нельзя менять тип после регистрации участников')
    for k,v in data.model_dump().items(): setattr(o,k,v)
    audit(db,u,'UPDATE_OLYMPIAD',oid); db.commit(); return serialize(o)

@app.get('/api/admin/olympiads/{oid}/dashboard')
def dashboard(oid:str,u:User=Depends(admin),db:DBSession=Depends(get_db)):
    get_or_404(db,Olympiad,oid)
    regs=list(db.scalars(select(Registration).where(Registration.olympiad_id==oid)))
    attempts=list(db.scalars(select(Attempt).join(Registration,Attempt.registration_id==Registration.id).where(Registration.olympiad_id==oid)))
    return {'registered':len(regs),'course_1':sum(r.course==1 for r in regs),'course_2':sum(r.course==2 for r in regs),'started':len(attempts),'finished':sum(a.finished or a.deadline<=now() for a in attempts),'submissions':db.scalar(select(func.count()).select_from(Submission).where(Submission.olympiad_id==oid)),'violations':db.scalar(select(func.count()).select_from(AntiCheatEvent).where(AntiCheatEvent.olympiad_id==oid))}

@app.get('/api/admin/olympiads/{oid}/participants')
def participants(oid:str,q:str='',level:int|None=None,u:User=Depends(admin),db:DBSession=Depends(get_db)):
    rows=[]
    for r in db.scalars(select(Registration).where(Registration.olympiad_id==oid)):
        user=db.get(User,r.user_id)
        if q.lower() not in f'{user.last_name} {user.first_name} {user.email} {user.organization}'.lower(): continue
        if level is not None and level not in (r.course,r.school_class): continue
        rows.append(serialize(r)|{'user':user_data(user)})
    return rows

@app.put('/api/admin/participants/{rid}')
def edit_participant(rid:str,data:ParticipantInput,u:User=Depends(admin),db:DBSession=Depends(get_db)):
    r=get_or_404(db,Registration,rid); o=db.get(Olympiad,r.olympiad_id)
    if o.type=='SCHOOL' and (data.school_class not in o.allowed_classes or data.course is not None): raise HTTPException(422,'Некорректный класс')
    if o.type=='SPO' and (data.course not in (1,2) or data.school_class is not None): raise HTTPException(422,'Некорректный курс')
    r.status=data.status; r.school_class=data.school_class; r.course=data.course; r.group=data.group
    db.get(User,r.user_id).organization=data.organization
    audit(db,u,'UPDATE_PARTICIPANT',rid); db.commit(); return serialize(r)

@app.post('/api/admin/participants/{rid}/reset-session/{sid}')
def reset_session(rid:str,sid:str,u:User=Depends(admin),db:DBSession=Depends(get_db)):
    a=db.scalar(select(Attempt).where(Attempt.registration_id==rid,Attempt.stage_id==sid).with_for_update())
    if not a: raise HTTPException(404,'Попытка не найдена')
    # Admin recovery permits the participant's next start to bind a new session, preserving deadline.
    checkpoint(db,a,db.get(Stage,sid)); a.active_task_id=None; a.session_hash=''; audit(db,u,'RESET_SESSION',a.id); db.commit(); return {'message':'Сессия освобождена'}

@app.get('/api/admin/olympiads/{oid}/export')
def export(oid:str,format:str='csv',u:User=Depends(admin),db:DBSession=Depends(get_db)):
    output=io.StringIO(); writer=csv.writer(output); writer.writerow(['ID','ФИО','Email','Организация','Класс','Курс','Статус','Баллы'])
    scores={r['participant_id']:r['score'] for r in ranking(db,oid)}
    def safe(v):
        s=str(v or ''); return "'"+s if s.startswith(('=','+','-','@','\t','\r')) else s
    for r in participants(oid,'',None,u,db):
        p=r['user']; writer.writerow([safe(x) for x in [r['id'],p['last_name']+' '+p['first_name'],p['email'],p['organization'],r['school_class'],r['course'],r['status'],scores.get(r['id'],0)]])
    if format=='xlsx':
        from openpyxl import Workbook
        workbook=Workbook(); sheet=workbook.active; sheet.title='Участники'
        for row in csv.reader(io.StringIO(output.getvalue())): sheet.append(row)
        blob=io.BytesIO(); workbook.save(blob)
        return Response(blob.getvalue(),media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={'Content-Disposition':'attachment; filename=participants.xlsx'})
    if format!='csv': raise HTTPException(422,'Допустимы csv и xlsx')
    return Response('\ufeff'+output.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename=participants.csv'})

@app.get('/api/admin/olympiads/{oid}/stages')
def admin_stages(oid:str,u:User=Depends(admin),db:DBSession=Depends(get_db)):
    return [serialize(s) for s in db.scalars(select(Stage).where(Stage.olympiad_id==oid).order_by(Stage.starts_at))]

@app.post('/api/admin/olympiads/{oid}/stages',status_code=201)
def create_stage(oid:str,data:StageInput,u:User=Depends(admin),db:DBSession=Depends(get_db)):
    get_or_404(db,Olympiad,oid); s=Stage(olympiad_id=oid,**data.model_dump()); db.add(s); db.flush(); audit(db,u,'CREATE_STAGE',s.id); db.commit(); return serialize(s)

@app.put('/api/admin/stages/{sid}')
def update_stage(sid:str,data:StageInput,u:User=Depends(admin),db:DBSession=Depends(get_db)):
    s=get_or_404(db,Stage,sid)
    if db.scalar(select(func.count()).select_from(Attempt).where(Attempt.stage_id==sid)): raise HTTPException(409,'Этап уже начат участниками; изменение сроков запрещено')
    for k,v in data.model_dump().items(): setattr(s,k,v)
    audit(db,u,'UPDATE_STAGE',sid); db.commit(); return serialize(s)

@app.get('/api/admin/stages/{sid}/tasks')
def admin_tasks(sid:str,u:User=Depends(admin),db:DBSession=Depends(get_db)):
    return [serialize(t)|{'tests':[serialize(c) for c in db.scalars(select(TestCase).where(TestCase.task_id==t.id))]} for t in ordered_tasks(db.scalars(select(Task).where(Task.stage_id==sid)))]

@app.get('/api/admin/task-packs/academy')
def academy_pack(audience:Literal['SCHOOL','SPO']='SPO',u:User=Depends(admin)):
    return {k:v for k,v in category_pack(audience).items() if k!='finale'}

@app.post('/api/admin/adventures/academy',status_code=201)
def install_academy(data:AcademyInput,u:User=Depends(admin),db:DBSession=Depends(get_db)):
    try:
        event,created=create_academy(db,data.type)
        if created: audit(db,u,'CREATE_ACADEMY',event.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        event=db.get(Olympiad,academy_id(data.type))
        if not event: raise
        created=False
    return {'olympiad':serialize(event),'created':created}

@app.post('/api/admin/stages/{sid}/tasks',status_code=201)
def create_task(sid:str,data:TaskInput,u:User=Depends(admin),db:DBSession=Depends(get_db)):
    s=get_or_404(db,Stage,sid)
    if db.scalar(select(func.count()).select_from(Attempt).where(Attempt.stage_id==sid)): raise HTTPException(409,'Нельзя добавлять задания после начала этапа участниками')
    t=Task(stage_id=sid,olympiad_id=s.olympiad_id,**data.model_dump(exclude={'tests'})); db.add(t); db.flush()
    for c in data.tests: db.add(TestCase(task_id=t.id,**c.model_dump()))
    audit(db,u,'CREATE_TASK',t.id); db.commit(); return serialize(t)

@app.put('/api/admin/tasks/{tid}')
def edit_task(tid:str,data:TaskInput,u:User=Depends(admin),db:DBSession=Depends(get_db)):
    t=get_or_404(db,Task,tid)
    if db.scalar(select(func.count()).select_from(Attempt).where(Attempt.stage_id==t.stage_id)): raise HTTPException(409,'Нельзя менять задание после начала этапа участниками')
    for k,v in data.model_dump(exclude={'tests'}).items(): setattr(t,k,v)
    db.execute(delete(TestCase).where(TestCase.task_id==tid))
    for c in data.tests: db.add(TestCase(task_id=tid,**c.model_dump()))
    audit(db,u,'UPDATE_TASK',tid); db.commit(); return serialize(t)

@app.get('/api/admin/olympiads/{oid}/submissions')
def admin_submissions(oid:str,u:User=Depends(admin),db:DBSession=Depends(get_db)):
    rows=[]
    for s in db.scalars(select(Submission).where(Submission.olympiad_id==oid).order_by(Submission.created_at.desc()).limit(500)):
        task=db.get(Task,s.task_id); user=db.get(User,s.user_id)
        rows.append(serialize(s,('code',))|{'task_title':task.title,'kind':task.kind,'max_points':task.points,'participant_name':user.last_name+' '+user.first_name})
    return rows

@app.get('/api/admin/olympiads/{oid}/task-times')
def admin_task_times(oid:str,u:User=Depends(admin),db:DBSession=Depends(get_db)):
    get_or_404(db,Olympiad,oid)
    timestamp=now(); rows=[]
    for attempt in db.scalars(select(Attempt).join(Registration,Registration.id==Attempt.registration_id).where(Registration.olympiad_id==oid)):
        r=db.get(Registration,attempt.registration_id); user=db.get(User,r.user_id); stage=db.get(Stage,attempt.stage_id)
        times={t['task_id']:t for t in snapshot(db,attempt,stage,timestamp)['timings']}
        for task in ordered_tasks(db.scalars(select(Task).where(Task.stage_id==stage.id))):
            rows.append({'participant_id':r.id,'participant_name':user.last_name+' '+user.first_name,'email':user.email,'stage_title':stage.title,'task_title':task.title,'task_id':task.id,'kind':task.kind,**times.get(task.id,{'elapsed_ms':0,'active_until':None})})
    return {'timings':rows,'server_time':timestamp}


@app.get('/api/admin/olympiads/{oid}/events')
def admin_events(oid:str,u:User=Depends(admin),db:DBSession=Depends(get_db)):
    return [serialize(e) for e in db.scalars(select(AntiCheatEvent).where(AntiCheatEvent.olympiad_id==oid).order_by(AntiCheatEvent.timestamp.desc()).limit(1000))]

@app.get('/api/admin/olympiads/{oid}/ranking')
def admin_ranking(oid:str,u:User=Depends(admin),db:DBSession=Depends(get_db)): return ranking(db,oid)

@app.get('/api/admin/audit')
def audit_logs(u:User=Depends(admin),db:DBSession=Depends(get_db)):
    return [serialize(a) for a in db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(500))]
