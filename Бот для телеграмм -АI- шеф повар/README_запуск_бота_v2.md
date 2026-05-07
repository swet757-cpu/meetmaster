# Запуск Telegram-бота ИИ-шеф в n8n

Результат: файл `n8n_ai_chef_bot_workflow_v2.json` можно импортировать в n8n на вашем сервере.

## Что найдено в образце

В файле `образец .docx` лежит скриншот workflow n8n:

| Узел | Роль |
|---|---|
| Telegram Trigger | принимает сообщения из Telegram |
| AI Agent | формирует ответ шеф-повара |
| OpenAI Chat Model | модель чата для агента |
| Simple Memory | память диалога по chat id |
| Send Telegram Message | отправляет ответ пользователю |

## Как включить на сервере

1. Откройте n8n на сервере.
2. Нажмите `Import from file`.
3. Выберите `n8n_ai_chef_bot_workflow_v2.json`.
4. В узлах `Telegram Trigger` и `Send Telegram Message` выберите Telegram credential.
5. В узле `OpenAI Chat Model` выберите OpenAI credential.
6. Нажмите `Test workflow` и отправьте сообщение боту в Telegram.
7. Если тест прошел, нажмите `Active`.

## Импорт через API сервера

Можно импортировать через `import_n8n_workflow_v2.ps1`.

Сначала задайте переменные окружения в PowerShell:

```powershell
$env:N8N_URL = "https://ваш-домен-n8n"
$env:N8N_API_KEY = "ваш-api-key"
.\import_n8n_workflow_v2.ps1
```

Скрипт создаёт workflow неактивным. После импорта выберите credentials в n8n и включите workflow вручную.

## Проверка

Напишите боту:

```text
У меня есть курица, рис и помидоры. Что приготовить на ужин?
```

Ожидаемый ответ: бот предложит рецепт, порции, время и шаги приготовления.

## Если не заработало

| Симптом | Что проверить |
|---|---|
| Telegram Trigger не получает сообщения | токен Telegram-бота и webhook в n8n |
| AI Agent красный или не запускается | подключен ли `OpenAI Chat Model` к входу `Model` |
| Ошибка OpenAI | выбран ли OpenAI credential и есть ли доступ к модели |
| Ответ не отправляется в Telegram | выбран ли Telegram credential в `Send Telegram Message` |

Секреты, токены и API-ключи не храните в файлах проекта. Добавляйте их только в credentials n8n.
