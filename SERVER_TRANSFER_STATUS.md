# MeetMaster: статус проверки сервера и переноса

## Update 2026-05-14 after support added the key

Support said the public key was added to `/root/.ssh/authorized_keys`, but SSH login from this workstation still fails:

```text
root@155.212.135.186: Permission denied (publickey).
```

Verbose SSH diagnostics confirm that the local client offers this key:

```text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJjJbwFTKNxMZOtrcvg+f1BS61uI6l7JNL4FcF91mbfC meetmaster-beget
SHA256:tCMCVBgLGGFA8mYP+HX8E5GPJOLI9rxyxZgM/CVZL/k
```

The server rejects it before login. Ask support to verify on VPS `155.212.135.186`:

```bash
ls -ld /root /root/.ssh
ls -l /root/.ssh/authorized_keys
grep -n "meetmaster-beget" /root/.ssh/authorized_keys
sshd -T | grep -E "permitrootlogin|pubkeyauthentication|authorizedkeysfile|strictmodes"
tail -n 100 /var/log/auth.log
```

Expected safe permissions:

```bash
chown root:root /root /root/.ssh /root/.ssh/authorized_keys
chmod 700 /root/.ssh
chmod 600 /root/.ssh/authorized_keys
```

Local deployment package is committed and pushed to GitHub:

```text
032914f Add Docker deployment setup
```

Дата: 2026-05-13

## Цель

Проверить проект Telegram-бота MeetMaster, подготовить перенос на сервер Beget VPS через Docker и сделать это максимально без ручных действий со стороны владельца.

## Что уже проверено в проекте

1. Осмотрена структура проекта.
   - Python-проект.
   - Telegram-бот на aiogram.
   - База данных рассчитана на PostgreSQL.
   - Миграции Alembic уже есть.
   - Запуск бота: `python -m app.main`.

2. Проверены секреты и Git.
   - `.env` не отслеживается Git.
   - `credentials/` не отслеживается Git.
   - `local_data/` не отслеживается Git.
   - Рабочее дерево Git было чистым до добавления служебных файлов.

3. Выполнены локальные проверки.
   - `pytest`: 19 тестов прошли.
   - `compileall`: код компилируется.
   - `ruff`: ошибок нет.

4. Найден небольшой косметический момент.
   - README в консоли отображается с битой кодировкой, но на работу бота это не влияет.

## Что уже сделано для доступа к серверу

1. Найден сервер Beget VPS:
   - IP: `155.212.135.186`
   - подключение: `root@155.212.135.186`
   - имя сервера в панели: `тестирование сервиса`
   - ОС: Ubuntu 24.04

2. Проверено, что сервер отвечает.
   - `ping` проходит.
   - SSH-порт отвечает.
   - Сервер отвечает как Ubuntu/OpenSSH.

3. Обнаружено, что SSH не принимает пароль.
   - Ошибка: `Permission denied (publickey)`.
   - Это значит, что сервер принимает только SSH-ключ.

4. Был сброшен пароль root через панель Beget.
   - Пароль не записан в этот файл специально.
   - После перезагрузки SSH всё равно принимает только `publickey`.

5. Сервер был перезагружен через панель Beget.
   - После перезагрузки сервер снова отвечает.
   - Парольный SSH-вход всё равно не включился.

6. Установлен PuTTY на локальный компьютер.
   - Это нужно, чтобы после появления доступа я мог подключиться через `plink` и выполнить проверочные команды сам.

7. Создан временный SSH-ключ для доступа.
   - Публичный ключ:

```text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJjJbwFTKNxMZOtrcvg+f1BS61uI6l7JNL4FcF91mbfC meetmaster-beget
```

   - Приватный ключ лежит локально в `.deploy_keys/`.
   - `.deploy_keys/` добавлен в `.gitignore`, чтобы ключ случайно не попал на GitHub.

## Почему нельзя переустанавливать сервер

В панели Beget видно, что на VPS занято примерно `21.1 ГБ из 25 ГБ`.

Это значит, что на сервере уже есть данные. Пока неизвестно, что именно там хранится, поэтому:

- не нажимать `Переустановить`;
- не удалять сервер;
- не включать действия, которые стирают диск.

Переустановка Docker-образа удалит данные на VPS.

## Текущий блокер

Нужно попасть на сервер, чтобы посмотреть файлы.

Сейчас:

- браузерный терминал работает нестабильно;
- файловый менеджер Beget выдает ошибку `Unable to load settings`;
- SSH по паролю не работает;
- временный SSH-ключ пока не добавлен на сервер.

## Обновление после ответа поддержки Beget

Поддержка Beget ответила, что через VNC-терминал можно войти с root-паролем, потому что ограничения SSH на VNC не распространяются.

Что удалось:

1. В VNC-терминал удалось войти под пользователем `root`.
2. Было видно, что сервер работает на Ubuntu 24.04.4 LTS.
3. В панели/консоли видно, что диск занят примерно на 88%, около `21 ГБ` из `23-25 ГБ`.
4. Было подтверждено, что сервер живой и не переустановлен.

Что не удалось:

1. Автоматически ввести команды в VNC из локального компьютера надежно не получилось.
2. Попытка вручную включить парольный SSH была выполнена частично:

```bash
cd /etc/ssh/sshd_config.d
echo PasswordAuthentication yes > 00-root.conf
echo PermitRootLogin yes >> 00-root.conf
service ssh restart
```

3. После этого внешний SSH всё равно отвечал только:

```text
publickey
```

То есть подключиться с компьютера к серверу всё еще не получилось.

Последняя проверка в конце дня: внешний SSH всё еще отвечает `server sent: publickey`, парольный вход не включился.

Важно: на сервере мог остаться временный файл:

```text
/etc/ssh/sshd_config.d/00-root.conf
```

Его нужно либо проверить, либо удалить после восстановления нормального доступа. Это должен сделать человек с доступом через VNC или поддержка Beget.

Рекомендуемый текст для поддержки теперь:

```text
Здравствуйте. Через VNC удалось войти под root. Мы пытались временно включить парольный SSH через файл /etc/ssh/sshd_config.d/00-root.conf:

PasswordAuthentication yes
PermitRootLogin yes

После service ssh restart внешний SSH всё равно принимает только publickey.
Пожалуйста, помогите:
1. добавить SSH-ключ для root без переустановки сервера;
2. проверить, почему SSH не принимает пароль;
3. при необходимости удалить временный файл /etc/ssh/sshd_config.d/00-root.conf;
4. не переустанавливать сервер, потому что на диске занято около 21 ГБ и там могут быть важные данные.

Публичный ключ:
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJjJbwFTKNxMZOtrcvg+f1BS61uI6l7JNL4FcF91mbfC meetmaster-beget
```

## Что нужно сделать дальше

### Вариант 1: через поддержку Beget, самый безопасный

Написать в поддержку Beget:

```text
Здравствуйте. На VPS "тестирование сервиса" 155.212.135.186 нужно проверить файлы перед переносом проекта.
На диске занято около 21.1 ГБ из 25 ГБ, поэтому переустанавливать сервер нельзя.
После сброса пароля root и перезагрузки SSH всё равно принимает только publickey, парольный вход не доступен.
Браузерный терминал работает нестабильно, файловый менеджер выдаёт "Unable to load settings".

Пожалуйста, добавьте публичный SSH-ключ для root без переустановки сервера или включите парольный SSH-доступ.
Ключ:
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJjJbwFTKNxMZOtrcvg+f1BS61uI6l7JNL4FcF91mbfC meetmaster-beget
```

После ответа поддержки:

1. Если ключ добавлен, подключиться:

```powershell
ssh -i .deploy_keys\meetmaster_beget_ed25519 root@155.212.135.186
```

2. Если включен парольный SSH, подключиться:

```powershell
ssh root@155.212.135.186
```

### Вариант 2: через Rescue-режим

Использовать только если поддержка не поможет.

Rescue-режим позволяет посмотреть диск без переустановки, но для новичка он рискованнее, потому что можно перепутать диск или команды. Лучше делать его только вместе с пошаговой инструкцией.

## Команды для проверки сервера после получения доступа

Только читающие команды, ничего не удаляют:

```bash
whoami
hostname
uname -a
cat /etc/os-release
df -h
du -h --max-depth=1 / 2>/dev/null
ls -la /root
ls -la /home
ls -la /opt
docker --version || true
docker compose version || true
docker ps -a || true
```

Цель этих команд:

- понять, что занимает 21 ГБ;
- найти пользовательские файлы;
- проверить, установлен ли Docker;
- понять, можно ли переносить бота без переустановки сервера.

## План переноса бота через Docker после проверки сервера

1. Сначала сохранить или перенести важные файлы с VPS, если они там есть.
2. Docker-файлы уже добавлены в проект:
   - `Dockerfile`
   - `docker-compose.yml`
   - `.dockerignore`
   - `.gitattributes`
   - `docker-entrypoint.sh`
3. В `docker-compose.yml` уже описаны два сервиса:
   - `bot` - Telegram-бот;
   - `db` - PostgreSQL.
4. `docker-entrypoint.sh` ждет готовности PostgreSQL, применяет Alembic-миграции и запускает бота.
5. Настройки и секреты оставить в `.env` на сервере, не добавлять их в GitHub.
6. На сервере клонировать проект из GitHub.
7. Запустить:

```bash
docker compose up -d --build
```

Миграции применяются автоматически при старте контейнера `bot`. Если нужно запустить их вручную:

```bash
docker compose exec bot alembic upgrade head
```

8. Проверить логи:

```bash
docker compose logs -f bot
```

9. После успешного запуска проверить Telegram-бота вручную в Telegram.

## Важные правила безопасности

- Не хранить пароли в документах и GitHub.
- Не отправлять `.env`, Telegram token и Google credentials в обычные чаты.
- Не нажимать `Переустановить`, пока не проверены данные на VPS.
- Не удалять старые файлы на сервере, пока не понятно, что это.
- Перед переносом через Docker лучше сделать снапшот VPS, если Beget позволяет.
