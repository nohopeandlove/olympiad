from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = 'postgresql+psycopg://olympiad:development@postgres/olympiad'
    redis_url: str = 'redis://redis:6379/0'
    app_env: str = 'development'
    public_origin: str = 'http://localhost:8080'
    judge_url: str = 'http://judge:9000'
    judge_token: str = ''
    smtp_host: str = ''
    smtp_port: int = 1025
    smtp_user: str = ''
    smtp_password: str = ''
    smtp_from: str = 'olympiad@localhost'
    smtp_starttls: bool = False
    model_config = {'env_file': '.env', 'extra': 'ignore'}

settings = Settings()

if settings.app_env=='production':
    if not settings.public_origin.startswith('https://'): raise RuntimeError('Production требует HTTPS PUBLIC_ORIGIN')
    if len(settings.judge_token)<32 or settings.judge_token.startswith('dev-'): raise RuntimeError('Задайте случайный JUDGE_TOKEN минимум 32 символа')
    if ':development@' in settings.database_url: raise RuntimeError('Замените development пароль БД')
    if not settings.smtp_host or settings.smtp_host=='mailpit': raise RuntimeError('Настройте production SMTP')
