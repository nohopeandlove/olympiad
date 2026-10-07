import os
from datetime import date, timedelta
from sqlalchemy import select
from .db import SessionLocal
from .models import *
from .security import hasher
from .config import settings

PASSWORD='DevOnly!Python2026'
def main():
    if settings.app_env!='development': raise RuntimeError('Development seed запрещён в production')
    with SessionLocal() as db:
        if db.scalar(select(Olympiad)): print('Seed уже существует'); return
        users=[]
        for email,last,first,role in [('admin@example.org','Администратор','Платформы','admin'),('school@example.org','Иванов','Алексей','participant'),('spo1@example.org','Петрова','Мария','participant'),('spo2@example.org','Смирнов','Дмитрий','participant')]:
            u=User(email=email,password_hash=hasher.hash(PASSWORD),last_name=last,first_name=first,role=role,birth_date=date(2008,5,15),phone='+79000000000',region='Свердловская область',city='Екатеринбург',organization='Демонстрационная образовательная организация',verified=True)
            db.add(u); db.flush(); users.append(u)
        for typ,title in [('SCHOOL','Олимпиада для школьников'),('SPO','Олимпиада для студентов СПО')]:
            o=Olympiad(type=typ,title=title,description='Решайте задачи на Python, развивайте алгоритмическое мышление и соревнуйтесь с участниками своего уровня.',rules='## Правила\nРешайте задания самостоятельно на Python 3. Не передавайте условия и решения другим участникам. Время этапа контролируется сервером. События браузера рассматриваются организаторами и сами по себе не являются доказательством нарушения.',status='active',registration_start=now()-timedelta(days=1),registration_end=now()+timedelta(days=7),ranking_visible=True)
            db.add(o); db.flush()
            for idx,kind in enumerate(['qualifying','main']):
                s=Stage(olympiad_id=o.id,title='Отборочный этап' if idx==0 else 'Основной этап',kind=kind,starts_at=now()-timedelta(hours=1) if idx==0 else now()+timedelta(days=8),ends_at=now()+timedelta(days=7 if idx==0 else 9),duration_minutes=120); db.add(s); db.flush()
                tasks=[('Сумма двух чисел','Даны два целых числа. Выведите их сумму.','Два целых числа через пробел.','Одно целое число.','2 3\n','5\n','-10 7\n','-3\n'),('Максимум последовательности','Найдите максимальное число в последовательности.','Числа через пробел.','Максимальное число.','1 9 3\n','9\n','-8 -2 -5\n','-2\n')] if typ=='SCHOOL' else [('Сумма квадратов','Вычислите сумму квадратов заданных чисел.','Целые числа через пробел.','Сумма квадратов.','1 2 3\n','14\n','-2 0 4\n','20\n'),('Уникальные значения','Подсчитайте количество различных целых чисел.','Целые числа через пробел.','Количество различных чисел.','1 2 2 3\n','3\n','5 5 5\n','1\n')]
                for title,statement,inp,out,pi,po,hi,ho in tasks:
                    t=Task(olympiad_id=o.id,stage_id=s.id,title=title,statement=statement,input_description=inp,output_description=out,constraints='|aᵢ| ≤ 10⁶; количество чисел ≤ 10⁴'); db.add(t); db.flush()
                    db.add_all([TestCase(task_id=t.id,input=pi,expected=po,public=True),TestCase(task_id=t.id,input=hi,expected=ho,public=False)])
            for user,level in ([(users[1],10)] if typ=='SCHOOL' else [(users[2],1),(users[3],2)]):
                db.add(Registration(user_id=user.id,olympiad_id=o.id,school_class=level if typ=='SCHOOL' else None,course=level if typ=='SPO' else None))
        db.commit(); print('Development seed создан')
if __name__=='__main__': main()
