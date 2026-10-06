import hashlib, secrets
from datetime import timedelta
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session as DBSession
from redis import Redis
from .db import get_db
from .models import Session, User, now
from .config import settings

hasher = PasswordHasher()
dummy_hash = hasher.hash(secrets.token_urlsafe(32))
redis = Redis.from_url(settings.redis_url)
def digest(value): return hashlib.sha256(value.encode()).hexdigest()
def password_ok(value, hashed):
    try: return hasher.verify(hashed,value)
    except (VerifyMismatchError, InvalidHashError): return False

def limit(key, count, seconds):
    try:
        with redis.pipeline() as pipe:
            pipe.incr(key); pipe.expire(key, seconds, nx=True)
            total, _ = pipe.execute()
    except Exception:
        raise HTTPException(503,'Защита запросов недоступна')
    if total > count: raise HTTPException(429,'Слишком много запросов, попробуйте позже')

def current_user(request: Request, db: DBSession = Depends(get_db)):
    raw = request.cookies.get('session','')
    session = db.get(Session,digest(raw))
    if not session or session.expires_at <= now(): raise HTTPException(401,'Необходим вход')
    user = db.get(User,session.user_id)
    if not user or user.blocked: raise HTTPException(403,'Аккаунт заблокирован')
    if request.method not in ('GET','HEAD','OPTIONS'):
        if request.headers.get('origin') != settings.public_origin: raise HTTPException(403,'Недопустимый Origin')
        if not secrets.compare_digest(request.headers.get('x-csrf-token',''),session.csrf): raise HTTPException(403,'Ошибка CSRF')
    request.state.session = session
    return user

def admin(user: User = Depends(current_user)):
    if user.role != 'admin': raise HTTPException(403,'Требуются права администратора')
    return user

def new_session(db, user, response):
    raw = secrets.token_urlsafe(32)
    session = Session(id=digest(raw),user_id=user.id,csrf=secrets.token_urlsafe(32),expires_at=now()+timedelta(days=7))
    db.add(session); db.commit()
    response.set_cookie('session',raw,httponly=True,secure=settings.app_env=='production',samesite='lax',max_age=604800,path='/')
    return session.csrf

def exam_session(request):
    import re
    value=request.headers.get('x-exam-session','')
    if not re.fullmatch(r'[A-Za-z0-9_-]{20,100}',value): raise HTTPException(422,'Требуется идентификатор олимпиадной вкладки')
    return digest(request.state.session.id+':'+value)
