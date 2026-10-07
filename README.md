# Python Олимпиады

Одна сюжетная олимпиада «Сбой в Академии Алгоритмов» для школьников 10–11 классов и студентов СПО 1–2 курса. Интерфейс на русском. Две категории участия имеют отдельные регистрации, расписания и рейтинги; после входа участник видит только свою категорию. Отборочный этап включает 8 заданий, основной — 10. Школьная версия проще, версия СПО использует более сложные алгоритмы; контрольные вопросы тоже различаются. Старые мероприятия сохраняются в базе как история.

## Быстрый запуск

Требуются Docker Engine с рабочими cgroups v2, Docker Compose v2 и доступ к реестрам образов, PyPI и npm. Для запуска недоверенных решений используйте отдельную Linux-машину judge.

```bash
[ -f .env ] || cp .env.example .env
# Для development оставьте настройки примера; для production замените секреты.
docker compose up --build -d
docker compose exec backend python -m app.seed
```

Откройте сайт на порту 8080 своей машины. Mailpit (development-почта) работает на порту 8025. Регистрация отправляет письмо с одноразовой ссылкой, действующей 24 часа. Seed запускается явно, идемпотентен и запрещён при APP_ENV=production. Исходный `docker compose up --build` запускает сервисы, создаёт схему через Alembic; данные добавляет отдельный seed.

### Демонстрационные аккаунты — только development

| Аккаунт | Email | Пароль |
|---|---|---|
| Администратор | admin@example.org | DevOnly!Python2026 |
| Школьник, 10 класс | school@example.org | DevOnly!Python2026 |
| Студент СПО, 1 курс | spo1@example.org | DevOnly!Python2026 |
| Студент СПО, 2 курс | spo2@example.org | DevOnly!Python2026 |

Development seed создаёт активный отборочный этап с датами относительно момента запуска и основной этап в будущем. Результаты видны. Эти настройки нужны для проверки, не являются расписанием реального конкурса. Даты frontend получает из API, отображает в UTC+5 (Екатеринбург). Admin datetime-поля используют локальный часовой пояс браузера и отправляют ISO с UTC.

## Сюжет и виды заданий

Приключение с отборочным и основным этапами создаётся автоматически при обновлении базы. В админке организатор выбирает категорию участников и настраивает даты, задания и проверку ответов. Отборочный сочетает Python, выбор варианта и развёрнутые ответы с ручной оценкой. Участник и администратор видят накопленное время по заданиям. Порядок настройки, оценки и обновления старой установки: [docs/ACADEMY.md](docs/ACADEMY.md).

## Архитектура

```text
Браузер → Nginx → Next.js / FastAPI → PostgreSQL
                         FastAPI → Redis → Celery worker
                                            ↓ HTTP с JUDGE_TOKEN
                                          Judge gateway → одноразовый Docker sandbox
```

- Next.js 15, React 19, TypeScript, Tailwind 4, Monaco Editor (локальные ресурсы, без CDN), безопасный Markdown без raw HTML.
- FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL 16.
- Redis 7 — очередь Celery и атомарные ограничения частоты; сбой Redis закрывает операции с rate limiting.
- Celery worker читает тесты из БД и передаёт их judge. Backend и worker не имеют Docker socket.
- Judge gateway имеет Docker socket, но не включён в сеть БД и не имеет DB credentials. Socket даёт контроль над Docker-хостом: production judge должен быть на выделенном хосте, удалённый транспорт — TLS/mTLS, с ограниченным доступом worker.
- Nginx — единая точка входа; БД, Redis, worker и judge не публикуют порты.
- Compose-сервис `sandbox-image` собирает образ и завершается; каждое реальное исполнение создаёт отдельный контейнер.

## Модель БД

`users → olympiad_registrations → olympiads`. Уникальные email (нормализованы в нижний регистр), уникальная пара account/event. Регистрация хранит класс или курс и группу, статус и время согласия. Профиль относится к аккаунту.

`stages` привязаны к olympiad. `participants` — попытки конкретного этапа, уникальная пара registration/stage, started_at, deadline, session binding, finished. `tasks` содержат stage_id и olympiad_id; `test_cases` имеют public-флаг. `submissions` содержат user/event/stage/task, код, режим, статус, баллы. `submission_results` хранят безопасные сведения о проверке. Остальные таблицы: `drafts`, `sessions`, `email_verifications`, `notifications`, `anti_cheat_events`, `audit_logs`. Все основные связи используют внешние ключи; бизнес-проверки выполняются backend.

Первоначальная миграция: `backend/alembic/versions/0001_initial.py`. Она содержит зафиксированные PostgreSQL CREATE TABLE операции. При дальнейшем развитии добавляйте новые миграции, не меняя применённую initial миграцию.

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.create_admin
```

Создание admin запрашивает пароль интерактивно, не через аргументы командной строки. В production не запускайте development seed.

## Рабочие сценарии

На главной — карточки мероприятий. Страница олимпиады показывает актуальные правила и расписание. Формы SCHOOL и SPO различаются и не содержат наставника. В личном кабинете доступны регистрации, этапы, сроки, уведомления и история проверок; существующий аккаунт может регистрироваться на дополнительные события своей образовательной категории. Участник SCHOOL не может самостоятельно зарегистрироваться в SPO, и наоборот; backend проверяет это по существующим регистрациям. Аккаунт администратора может участвовать в обоих типах для проверки. Процедура смены образовательной категории при переходе из школы в СПО остаётся задачей будущего развития. Для SCHOOL обязателен разрешённый класс и отсутствуют course/group; для SPO разрешены только course=1/2 и отсутствует school_class.

Участник начинает этап явно. Сервер сохраняет `deadline=min(started_at+duration,stage_end)`. Обновление страницы и повторный `/start` не меняют время. Backend проверяет текущую регистрацию, подтверждённый email, статус олимпиады, период этапа, attempt и deadline на выдаче задач, сохранении черновика и создании submissions. Завершённый этап закрывается для отправок. Новая авторизованная сессия не перехватывает уже начатую попытку; администратор может освободить binding, не меняя deadline.

Admin-панель: выбор олимпиады, отдельная статистика (включая курсы СПО), настройки и видимость рейтинга, создание мероприятий, создание и редактирование этапов и заданий, редактор тестов, поиск и фильтрация участников, изменение организации/класса/курса/статуса, блокировка и дисквалификация регистрации, просмотр событий/решений, CSV/XLSX, рейтинг и аудит. Редактирование этапов и заданий после начала попыток запрещено, чтобы результаты оставались сопоставимыми. Удаление мероприятий и массовая рассылка не входят в MVP.

## Judge и scoring

«Запустить» проверяет публичные примеры, score=0. «Отправить» проверяет все тесты. Баллы: `points * passed // total`; официальный рейтинг складывает лучший балл по каждой задаче, строго в пределах olympiad_id. Код и результаты чужого submission недоступны участнику.

Статусы: Queued, Running, Accepted, Wrong Answer, Time Limit Exceeded, Memory Limit Exceeded, Runtime Error, Interpreter Error, System Error. Сравнение вывода игнорирует различия в пробелах (token comparison). Официальные результаты содержат только статусы тестов и количество пройденных: скрытые input/expected/stdout/stderr не отправляются клиенту. Публичный запуск возвращает ограниченные stdout/stderr.

Sandbox: `network=none`, root filesystem read-only, без host mounts/секретов/socket, CPU=1 core, 32–256 МБ с отключённым дополнительным swap, pids=16, CPU/wall time limits, fd/file size limits, stdout+stderr до 2 МиБ, tmpfs /tmp=8 МБ. По умолчанию Docker seccomp, все capabilities сняты кроме SETUID/SETGID/KILL для доверенного supervisor (смена пользователя и остановка дочернего процесса); сам пользовательский Python запускается с uid/gid 65534, без capabilities, с no-new-privileges. Supervisor передаёт JSON результата через свой stdout; пользовательский stdout/stderr захватывается отдельными pipes и не может подделать служебный канал. Docker logging ограничен 16 МиБ для JSON с экранированием Unicode. Полный ограниченный вывод сравнивается с ответом до обрезки; публичная консоль показывает до 16 384 символов stdout и 4096 символов stderr. Контейнер удаляется в finally, вместе с оставшимися процессами. Изоляция контейнера не является защитой от уязвимостей ядра: выделенный judge-хост обязателен перед публичным запуском; рассмотрите gVisor/Firecracker.

Два Celery процесса и два judge slots ограничивают параллелизм. System Error означает сбой инфраструктуры; в MVP нет автоматического восстановления зависших Running jobs после аварии worker и автоматического rejudge. Перед production добавьте reconciliation/rejudge, мониторинг и политику повторной обработки.

## Авторизация и безопасность

Пароли: Argon2id. Сессии: случайные opaque cookies, в БД только SHA-256 токена; HttpOnly, SameSite=Lax, Secure при APP_ENV=production. Изменяющие авторизованные API требуют CSRF token и точный Origin. Login/register проверяют Origin. Email-токены одноразовые и хешируются, email подтверждается перед входом. RBAC на backend, SQLAlchemy параметризует SQL; строгие Pydantic payloads; ограничены исходники, тесты, размеры запросов. Rate limiting защищает login (IP и email), регистрацию, submissions, autosave и события. Nginx перезаписывает X-Real-IP; backend доверяет этому заголовку только в закрытой сети Compose — не публикуйте backend напрямую.

Nginx задаёт CSP, frame-ancestors=none, nosniff, Referrer-Policy и Permissions-Policy. CSP разрешает inline script/style для Next.js и Monaco; для усиления внедрите nonce CSP перед production. Markdown не поддерживает raw HTML, React экранирует вывод. Экспорт защищён от формул электронных таблиц. Административные изменения записываются в audit_logs. `.env` игнорируется Git. Production configuration отклоняет HTTP origin, development пароль БД, demo judge token и Mailpit.

## Автосохранение, античит и ограничения

Черновик сохраняется в backend каждые 5 секунд и в localStorage по user/task. При обновлении локальный черновик имеет приоритет. Официальным результатом считается только submission. После deadline backend больше не принимает черновик; локальная копия остаётся. Очистка данных браузера уничтожает локальный fallback. На общих устройствах завершайте сеанс и очищайте локальные черновики.

Экран фиксирует копирование/вставку, context menu условия, TAB_HIDDEN, WINDOW_BLUR, FULLSCREEN_EXIT, CONNECTION_LOST; события потери сети передаются после восстановления. Выделение/редактирование собственного кода сохранено; context menu и копирование условия блокируются. Watermark содержит ФИО, ID регистрации и время, без телефона/email/даты рождения. Второй login session записывает событие и получает 409. Сервер привязывает attempt к хешу login session + случайному идентификатору вкладки. Он хранится в sessionStorage и сохраняется при reload. BroadcastChannel обнаруживает дублированную вкладку и выдаёт ей новый идентификатор; backend отклоняет вторую привязку. Идентификатор клиента можно намеренно скопировать, поэтому это не доказательство физической уникальности устройства.

Браузер не может гарантированно запретить системные скриншоты, второе устройство, DevTools, отключение JavaScript или подделку/блокировку телеметрии. События — повод для рассмотрения человеком, не доказательство нарушения. Нет автоматической дисквалификации. Fullscreen запрашивается по действию участника, не навязывается. Watermark лишь затрудняет распространение условий.

## Проверки

После запуска и seed:

`infra/test.sh` запускает обе серии и сбрасывает только временные development rate counters между ними. Сброс запрещён в production; ограничения остаются включёнными, тест отдельно проверяет ответ 429 после десяти неверных попыток.

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.lock
docker compose exec -T backend python -m app.reset_test_limits
cd backend
../.venv/bin/pytest -q
cd ../frontend
npm ci
npm run typecheck
npm run build
docker compose exec -T backend python -m app.reset_test_limits
npx playwright test
```

Integration tests работают с реальными PostgreSQL/Redis/Celery/judge, создают тестовые записи, проверяют письмо через Mailpit и предполагают development seed. Они не предназначены для production DB. Playwright использует системный Chromium (`CHROMIUM_PATH` позволяет выбрать другой путь); нужен установленный браузер. API tests изменяют сессии участников; перед browser tests восстановите их через admin reset-session или используйте чистый dev seed. `TEST_BASE_URL` задаёт адрес тестового сайта и должен совпадать с PUBLIC_ORIGIN.

## Переменные и production

`.env.example` описывает APP_ENV, PUBLIC_ORIGIN, POSTGRES_PASSWORD, JUDGE_TOKEN, SMTP_HOST/PORT/FROM/STARTTLS/USER/PASSWORD. DATABASE_URL, REDIS_URL и JUDGE_URL формируются Compose. Пароль PostgreSQL в URI не должен содержать специальные URI символы без кодирования; используйте случайную hex-строку. Для production: APP_ENV=production, HTTPS origin, уникальный пароль БД и случайный JUDGE_TOKEN (например, `openssl rand -hex 32`), настоящий SMTP с TLS и необходимыми credentials. Никогда не коммитьте `.env`.

Перед публичным запуском:

1. Разверните TLS termination, сертификаты, перенаправление HTTP→HTTPS и HSTS; текущий Nginx работает по HTTP для development и рассчитан на TLS reverse proxy перед ним. Настройте точный origin; не выставляйте backend/judge напрямую.
2. Изолируйте judge на отдельной машине, ограничьте доступ worker и Docker API, добавьте mTLS и проверку sandbox escape/нагрузки.
3. Замените demo credentials и не переносите seed в production. Настройте SMTP, процедуру восстановления пароля (пока отсутствует), срок хранения сессий и отзыв сессий.
4. Подготовьте реальные правила, политику персональных данных, согласие законного представителя несовершеннолетних, перечень публикуемых данных рейтинга и сроки удаления. Текст в development-форме не заменяет документы организатора.
5. Добавьте пагинацию больших наборов, durable reconciliation очереди, повторную проверку System Error, метрики, alerts, журнал доставки писем и transactional outbox для постановки jobs/email.
6. Проведите внешний security review, accessibility testing и нагрузочные проверки. Привязка учитывает login session и идентификатор вкладки; для контроля зависших вкладок внедрите lease/heartbeat и процедуру безопасного перехвата после истечения lease.
7. CSP nonce, secrets manager, retention и шифрование backup. Защитите администраторов MFA (в MVP отсутствует).

## Backup

```bash
mkdir -p /safe/backup
# Каталог backup должен быть закрыт для других пользователей.
docker compose exec -T postgres pg_dump -U olympiad -d olympiad -Fc > /safe/backup/olympiad.dump
# Восстанавливайте в отдельную проверочную БД и проверяйте до замены production.
docker compose exec -T postgres pg_restore -U olympiad -d olympiad --clean --if-exists < /safe/backup/olympiad.dump
```

Backup содержит персональные данные и код решений. Ограничьте права доступа, шифруйте, храните вне Docker-хоста, регулярно проверяйте восстановление. Не используйте `docker compose down -v` на важных данных.

## Облачная среда Codex

В этой среде proxy CA передаётся Docker BuildKit как необязательный `build_ca` secret. Локальный override хранится вне репозитория: `/workspace/olympiad-local/compose.cloud.yaml`. Это сохраняет TLS-проверку, не добавляет сертификаты конкретного облака в Git. При обычном запуске без перехватывающего прокси `docker compose up --build` использует стандартное системное доверие образов.

```bash
BUILDX_CONFIG=/workspace/.docker-buildx docker compose -f compose.yaml -f /workspace/olympiad-local/compose.cloud.yaml up --build -d
```

Используйте существующий checkout `/workspace/olympiad`; облачная задача уже изолирована, дополнительный worktree не требуется. После восстановления snapshot процессы надо запускать снова. Инструкции установки и старта сохраняются отдельно в настройках среды; публикация выполняется пользователем.

Результаты проведённой проверки: [docs/VALIDATION.md](docs/VALIDATION.md).

## Приключение Академии Алгоритмов

Восемь задач с единым сюжетом, готовым набором проверок и финалом после принятого решения последней главы. В админке выберите аудиторию и нажмите «Создать приключение». Перед публикацией проверьте даты этапа и регистрации. Подробные правила задач и порядок обновления: [docs/ACADEMY.md](docs/ACADEMY.md).
