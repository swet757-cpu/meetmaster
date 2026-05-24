# Инструкция: как создавалось Telegram Mini App для MeetMaster

Дата: 2026-05-14

Эта инструкция описывает весь путь создания Mini App в Telegram: от подготовки бота до запуска на сервере и обновления дизайна.

## 1. Что такое Mini App в нашем проекте

Telegram Mini App - это веб-страница, которая открывается внутри Telegram. В нашем случае это календарь встреч MeetMaster.

Пользователь открывает Mini App из бота, выбирает:

- дату встречи;
- длительность;
- свободное время;
- email участника;
- тему или описание встречи.

После отправки создаётся заявка, администратор получает уведомление в Telegram, а после подтверждения встреча добавляется в Google Calendar.

## 2. Общая схема работы

В проекте есть две части:

1. Telegram-бот на `aiogram`.
2. Mini App на `FastAPI` + обычный HTML/CSS/JS.

Mini App работает отдельно от основного бота:

```text
Telegram -> кнопка в боте -> Mini App HTTPS URL -> FastAPI -> база данных -> уведомление админу
```

Основной бот продолжает работать как раньше. Mini App добавлен как отдельный удобный интерфейс.

## 3. Файлы Mini App

Основные файлы:

```text
app/mini_app/api.py
app/services/mini_app_booking_service.py
app/services/telegram_webapp_auth.py
mini_app/frontend/index.html
mini_app/frontend/styles.css
mini_app/frontend/app.js
Dockerfile.miniapp
docker-compose.miniapp.yml
```

Что за что отвечает:

- `app/mini_app/api.py` - API Mini App и отдача HTML-страницы.
- `app/services/mini_app_booking_service.py` - логика дат, слотов и создания заявок.
- `app/services/telegram_webapp_auth.py` - проверка, что Mini App открыт настоящим пользователем Telegram.
- `mini_app/frontend/index.html` - разметка интерфейса.
- `mini_app/frontend/styles.css` - внешний вид.
- `mini_app/frontend/app.js` - выбор дат, времени, отправка заявки.
- `Dockerfile.miniapp` - сборка отдельного контейнера Mini App.
- `docker-compose.miniapp.yml` - запуск Mini App рядом с ботом.

## 4. Подготовка Telegram-бота

Сначала нужен обычный Telegram-бот, созданный через BotFather.

Нужно иметь:

- токен бота;
- команду или кнопку, которая открывает Mini App;
- публичный HTTPS-адрес Mini App.

В нашем проекте адрес хранится в `.env`:

```env
MINI_APP_URL=https://155.212.135.186.nip.io
```

Когда пользователь пишет команду `/mini_app`, бот отправляет кнопку открытия календаря.

## 5. Backend Mini App

Backend сделан на FastAPI.

Главный файл:

```text
app/mini_app/api.py
```

Он создаёт API:

```text
GET  /
GET  /api/me
GET  /api/booking/dates
GET  /api/booking/durations
GET  /api/booking/slots?target_date=YYYY-MM-DD&duration=45
POST /api/booking/requests
GET  /api/booking/my-requests
```

Главные задачи backend:

- отдать страницу Mini App;
- проверить Telegram `initData`;
- вернуть доступные даты;
- вернуть доступные длительности;
- вернуть свободные слоты времени;
- принять заявку;
- сохранить заявку в базу;
- отправить уведомление администратору.

## 6. Проверка пользователя Telegram

Mini App передаёт backend специальную строку `initData`.

Frontend отправляет её в заголовке:

```text
X-Telegram-Init-Data: <initData>
```

Backend проверяет подпись через токен бота. Это нужно, чтобы нельзя было просто открыть API снаружи и создать заявку от чужого имени.

Логика проверки находится здесь:

```text
app/services/telegram_webapp_auth.py
```

Для локальной разработки есть dev-режим:

```env
MINI_APP_DEV_MODE=true
MINI_APP_DEV_TELEGRAM_ID=8695348072
```

## 7. Логика записи на встречу

Основная логика находится здесь:

```text
app/services/mini_app_booking_service.py
app/services/slot_service.py
```

Сервис делает следующее:

- берёт рабочие дни;
- исключает выходные;
- исключает закрытые даты;
- учитывает минимальный срок записи;
- учитывает длительность встречи;
- учитывает уже занятые слоты;
- создаёт заявку со статусом ожидания подтверждения.

Длительности берутся из настроек:

```env
ALLOWED_DURATIONS=30,45,60
```

## 8. Frontend Mini App

Frontend находится здесь:

```text
mini_app/frontend/
```

Он сделан без сложных фреймворков: обычные `HTML`, `CSS`, `JavaScript`.

Страница:

```text
mini_app/frontend/index.html
```

Стили:

```text
mini_app/frontend/styles.css
```

Логика:

```text
mini_app/frontend/app.js
```

Frontend делает:

- загружает даты;
- загружает длительности;
- загружает свободное время;
- показывает вкладку записи;
- показывает вкладку моих заявок;
- отправляет заявку на backend.

## 9. Навигация по датам и времени

Чтобы интерфейс не растягивался внутри маленького окна Telegram, даты и время показываются страницами.

Сейчас используется:

```js
const MAX_VISIBLE_DATES = 6;
const MAX_VISIBLE_SLOTS = 6;
```

То есть:

- одновременно видно 6 дат;
- есть кнопки `Назад` и `Дальше`;
- одновременно видно 6 слотов времени;
- у времени тоже есть `Назад` и `Дальше`.

Это решило проблему, когда длинный список дат и времени перекрывал поля ввода.

## 10. Дизайн Mini App

Изначально дизайн был светлый и простой. Потом он был обновлён в более красивый тёмный ботанический стиль:

- тёмно-зелёный фон;
- мягкие панели;
- золотистые активные кнопки;
- крупные кнопки времени;
- аккуратные поля ввода;
- адаптация под маленькое окно Telegram.

Главный файл дизайна:

```text
mini_app/frontend/styles.css
```

Чтобы Telegram не показывал старый кеш, в `index.html` добавляется версия файлов:

```html
<link rel="stylesheet" href="/static/styles.css?v=20260514-2240" />
<script src="/static/app.js?v=20260514-2240"></script>
```

При каждом важном обновлении дизайна или JS лучше менять версию.

## 11. Локальный запуск

Для локальной проверки можно запустить Mini App так:

```powershell
.\scripts\run_mini_app_local.ps1
```

И открыть:

```text
http://127.0.0.1:8090/
```

Или вручную:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.mini_app.api:app --host 127.0.0.1 --port 8090
```

## 12. Проверка тестами

Для проверки Mini App запускались тесты:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_mini_app_booking_service.py
```

Ожидаемый результат:

```text
5 passed
```

## 13. Запуск на сервере

На сервере проект лежит здесь:

```text
/opt/meetmaster/app
```

Mini App запущен в Docker-контейнере:

```text
app-miniapp-1
```

Проверить контейнер:

```bash
docker ps --filter name=app-miniapp-1
```

Mini App внутри сервера слушает:

```text
127.0.0.1:8080
```

Публичный HTTPS-адрес:

```text
https://155.212.135.186.nip.io
```

## 14. Обновление Mini App на сервере

После изменения файлов frontend нужно переложить их на сервер:

```powershell
scp -i .deploy_keys\meetmaster_beget_ed25519 mini_app\frontend\app.js root@155.212.135.186:/opt/meetmaster/app/mini_app/frontend/app.js
scp -i .deploy_keys\meetmaster_beget_ed25519 mini_app\frontend\index.html root@155.212.135.186:/opt/meetmaster/app/mini_app/frontend/index.html
scp -i .deploy_keys\meetmaster_beget_ed25519 mini_app\frontend\styles.css root@155.212.135.186:/opt/meetmaster/app/mini_app/frontend/styles.css
```

Потом переложить их внутрь уже работающего контейнера:

```powershell
ssh -i .deploy_keys\meetmaster_beget_ed25519 root@155.212.135.186 "docker cp /opt/meetmaster/app/mini_app/frontend/app.js app-miniapp-1:/app/mini_app/frontend/app.js"
ssh -i .deploy_keys\meetmaster_beget_ed25519 root@155.212.135.186 "docker cp /opt/meetmaster/app/mini_app/frontend/index.html app-miniapp-1:/app/mini_app/frontend/index.html"
ssh -i .deploy_keys\meetmaster_beget_ed25519 root@155.212.135.186 "docker cp /opt/meetmaster/app/mini_app/frontend/styles.css app-miniapp-1:/app/mini_app/frontend/styles.css"
```

Так можно обновить интерфейс без пересборки контейнера.

## 15. Проверка после обновления

Проверить, что публичный сайт отдаёт новую версию:

```powershell
ssh -i .deploy_keys\meetmaster_beget_ed25519 root@155.212.135.186 "curl -ks https://155.212.135.186.nip.io/ | grep app.js"
```

Проверить, что JS содержит новую логику:

```powershell
ssh -i .deploy_keys\meetmaster_beget_ed25519 root@155.212.135.186 "curl -ks https://155.212.135.186.nip.io/static/app.js?v=20260514-2240 | grep MAX_VISIBLE_SLOTS"
```

Если всё хорошо, Telegram должен открыть обновлённый интерфейс.

## 16. Что делать, если Telegram показывает старую версию

Telegram может держать старую страницу в кеше.

Что помогает:

1. Полностью закрыть вкладку Mini App.
2. Открыть Mini App заново из бота.
3. Убедиться, что в `index.html` изменена версия `?v=...`.
4. Проверить публичный URL через `curl`.

Кнопка `Обновить` внутри Mini App обновляет данные, но не всегда перезагружает JS и CSS из кеша Telegram.

## 17. Сохранение изменений в Git

После каждого этапа изменения сохранялись в Git.

Основные коммиты:

```text
e4afb79 Add paged mini app date picker
703e44e Refresh mini app booking design
```

Отправка в GitHub:

```powershell
git push origin main
```

## 18. Итог

В результате получилось Telegram Mini App, которое:

- открывается внутри Telegram;
- показывает доступные даты;
- показывает доступное время;
- не растягивается и не перекрывает поля ввода;
- имеет навигацию по датам и времени;
- создаёт заявки на встречу;
- уведомляет администратора;
- работает на сервере по HTTPS;
- сохранено в GitHub.

