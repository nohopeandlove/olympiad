import getpass
from datetime import date
from sqlalchemy import select
from .models import User
from .db import SessionLocal
from .security import hasher

def main():
    email=input('Email администратора: ').strip().lower()
    password=getpass.getpass('Пароль (не менее 12 символов): ')
    if len(password)<12: raise ValueError('Пароль слишком короткий')
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email==email)): raise ValueError('Email уже существует')
        db.add(User(email=email,password_hash=hasher.hash(password),role='admin',last_name='Администратор',first_name='Платформы',birth_date=date(1990,1,1),phone='',region='',city='',organization='',verified=True)); db.commit()
if __name__=='__main__': main()
