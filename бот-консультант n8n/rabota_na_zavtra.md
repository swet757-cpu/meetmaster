# Работа на завтра

Дата обновления: 2026-05-08

## Итог на конец дня

Workflow `мой консультант` технически приведен к логике бота `Cash Flow Lifesaver`.

Основная схема уже настроена:

| Что | Статус |
|---|---|
| Логика бота прочитана | готово |
| Папка `assets` создана | готово |
| Файлы в `assets` проверены | готово |
| Google Drive подключен | готово |
| Папка Google Drive `Мой Спасатель` выбрана | готово |
| Таблица `knowledge_base` создана | готово |
| Ссылки на PDF и Google Таблицу записаны | готово |
| Таблица `documents_ai` создана | готово |
| Функция `match_documents_ai` создана | готово |
| Ошибка кэша Supabase REST исправлена | готово |
| Workflow обновлен под Cash Flow Lifesaver | готово |
| База `documents_ai` наполнена документами | не готово |
| Workflow активирован | не готово |

## Что сегодня точно поправлено

1. Прочитана логика бота из файлов:
   - `инструкция для бота_консультанта.docx`;
   - `assets/kb_cash_flow_lifesaver.txt`.

2. Подтверждена логика бота:
   - `emergency` — кассовый разрыв;
   - `profit_vs_cash` — прибыль есть, денег нет;
   - `calendar` — платежный календарь.

3. В `assets` лежат нужные файлы:
   - `checklist_cash_gap.pdf`;
   - `profit_vs_cash_guide.pdf`;
   - `kb_cash_flow_lifesaver.txt`.

4. В Supabase создана таблица `knowledge_base`.

5. В `knowledge_base` записаны ссылки:

| trigger_key | Материал |
|---|---|
| `emergency` | PDF-чек-лист «5 шагов при кассовом разрыве» |
| `profit_vs_cash` | PDF-гайд «прибыль vs деньги» |
| `calendar` | Google Таблица с платежным календарем |

6. В n8n workflow `мой консультант` заменен старый промпт агента.

7. Старый промпт был про курс `AI-навыки финансиста`.

8. Новый промпт теперь про `Cash Flow Lifesaver`.

9. Обновлено стартовое сообщение Telegram.

10. Обновлено описание инструмента `Supabase Vector Store1`.

11. Узлы Google Drive настроены на одну папку:
    - `Мой Спасатель`.

12. Исправлены оба Google Drive trigger:
    - `File Created`;
    - `File Updated`.

13. Оба узла теперь смотрят на один folder ID:
    - `1ZLK0_M4RP0eNB0-p3BSKiNnMBuxnyY9G`

14. Создана таблица Supabase:
    - `public.documents_ai`.

15. Создана функция Supabase:
    - `public.match_documents_ai`.

16. К узлам Supabase привязана учетная запись:
    - `Supabase account`.

17. К узлам Google Drive привязана учетная запись:
    - `Google Drive account`.

18. Создана учетная запись:
    - `OpenAI account`.

19. Сделана резервная копия workflow:
    - `workflow_entity_backup_codex_20260507`.

20. Дополнительно создана новая OpenAI-учетная запись:
    - `OpenAI account 2`.

21. Все OpenAI-узлы workflow переведены на:
    - `OpenAI account 2`.

22. Проверено, что `File Created` успешно получает тестовое событие из папки `Мой Спасатель`.

23. Проверено, что узлы проходят до шага:
    - `Delete Old Docs`;
    - `Download File`.

24. Выявлено и исправлено несоответствие в Supabase credentials:
    - раньше `Supabase account` смотрел в старый облачный Supabase;
    - теперь `Supabase account` смотрит на `https://supabase2.sweevottak.pro`.

## Какие ошибки нашли и как исправили

| Ошибка | Что было | Как исправлено |
|---|---|---|
| Старый промпт агента | Агент отвечал бы про курс, а не про кассовые разрывы | Промпт заменен на Cash Flow Lifesaver |
| Разные папки Google Drive | `File Created` и `File Updated` смотрели на разные папки | Оба узла переведены на `Мой Спасатель` |
| Не было `knowledge_base` | Ссылки некуда было записывать | Таблица создана и заполнена |
| Не было `documents_ai` | Векторная база не могла принимать документы | Таблица создана |
| Не было `match_documents_ai` | Агент не смог бы искать по базе | Функция создана |
| Supabase REST не видел `documents_ai` | n8n писал, что таблица не найдена в кэше схемы | Обновлен schema cache, перезапущен `supabase-rest`, выданы права |
| У Supabase-узлов не было credentials | `Delete Old Docs` и `Insert into Supabase Vectorstore` падали бы | Подключен `Supabase account` |
| У OpenAI-узлов не было credentials | Embeddings и чат-модель не имели учетной записи | Сначала подключен `OpenAI account`, потом workflow переведен на рабочий `OpenAI account 2` |
| Workflow запускался не той веткой | Красная кнопка запускала Telegram, а не загрузку документов | Зафиксировано: завтра запускать именно нижнюю ветку Google Drive |
| `Supabase account` смотрел не туда | n8n искал таблицу в другом Supabase-проекте `*.supabase.co` | Credential перенастроен на `https://supabase2.sweevottak.pro` |
| В `documents_ai` 0 строк | Документы еще не загружены в векторную базу | Причина найдена: ошибка quota в OpenAI embeddings |

## Важная новая проблема

OpenAI-ключ теперь вставлен в `OpenAI account 2`, и тест credentials проходит успешно.

Но при реальном выполнении embeddings сегодня получена ошибка квоты OpenAI.

Проверка показала:

| Проверка | Результат |
|---|---|
| `OpenAI account 2` | заполнен и connection test проходит |
| `Embeddings OpenAI` | падает в реальном запуске |
| Текст ошибки | `429 You exceeded your current quota` |
| Причина | у OpenAI API нет доступной квоты / биллинга для embeddings |

Значение ключа не выводилось и не записывалось.

## Памятка себе

1. Не трогать Google OAuth заново.

2. Не пересоздавать Supabase.

3. Не удалять workflow.

4. Не менять folder ID папки `Мой Спасатель`.

5. Не создавать вторую таблицу для документов.

6. Рабочая таблица для базы знаний:
   - `public.documents_ai`.

7. Рабочая функция поиска:
   - `public.match_documents_ai`.

8. Ссылки для кнопок лежат не в коде, а в:
   - `public.knowledge_base`.

9. Красная кнопка внизу n8n запускает Telegram-trigger, а не загрузку документов.

10. Чтобы загрузить файлы в базу, нужно запускать нижнюю ветку от Google Drive:
    - `File Created`;
    - или тестовый запуск узла с Google Drive file event.

11. Если в `documents_ai` 0 строк, агенту нечего искать в базе.

12. После любого создания таблицы Supabase нужно помнить про:
    - `notify pgrst, 'reload schema';`
    - при необходимости перезапуск `supabase-rest`.

13. `Supabase account` должен смотреть именно на:
    - `https://supabase2.sweevottak.pro`

14. Рабочая OpenAI credential сейчас:
    - `OpenAI account 2`

15. Если в workflow снова всплывет `OpenAI account`, надо проверить, не откатился ли узел на старую учетку.

16. Секреты не выводить:
    - OpenAI API key;
    - Supabase service role;
    - Google client secret;
    - Telegram token.

17. Если секрет случайно попал на скриншот или в чат, его нужно сменить.

## План на завтра

1. Открыть n8n.

2. Открыть credentials:
   - `OpenAI account 2`.

3. Проверить, что credential `OpenAI account 2` все еще сохранен и connection test успешный.

4. Открыть OpenAI billing.

5. Проверить, что для API есть активный способ оплаты или положительный баланс.

6. Если баланса нет — пополнить API-баланс.

7. Если есть лимит расходов — убедиться, что он не равен нулю.

8. Открыть workflow:
   - `мой консультант`.

9. Обновить страницу браузера.

10. Открыть узел:
   - `File Created`.

11. Проверить, что выбрана папка:
    - `Мой Спасатель`.

12. Запустить тест именно нижней ветки Google Drive.

13. Если тестового события нет:
    - загрузить новый тестовый файл в папку `Мой Спасатель`;
    - снова нажать тест события.

14. Дождаться прохода нижней ветки:
    - `File Created`;
    - `Loop Over Items`;
    - `Edit Fields3`;
    - `Delete Old Docs`;
    - `Download File`;
    - `Insert into Supabase Vectorstore`;
    - `Embeddings OpenAI`.

15. Проверить, что ошибка `429 quota` исчезла.

16. Проверить, что в `documents_ai` появились строки.

17. Если строки появились — проверить агента в Telegram:
    - `/start`;
    - «кассовый разрыв»;
    - «прибыль есть, а денег нет»;
    - «как вести платежный календарь».

18. Если ответы нормальные — нажать `Publish`.

19. Включить workflow.

20. После включения еще раз проверить Telegram.

## Что делать, если снова ошибка

| Ошибка | Что проверять |
|---|---|
| `documents_ai not found` | schema cache Supabase, права на таблицу, контейнер `supabase-rest` |
| `OpenAI credentials missing` | credential `OpenAI account 2` |
| `Invalid API key` | ключ OpenAI вставлен неверно или отозван |
| `429 You exceeded your current quota` | billing OpenAI API, баланс, лимиты usage |
| `Google Drive 403` | доступ Google Drive и включен ли Google Drive API |
| `No trigger output` | положить новый файл в папку `Мой Спасатель` |
| `0 rows in documents_ai` | нижняя ветка не загрузила документы |

## Что не делать завтра

1. Не начинать настройку с нуля.

2. Не создавать новый Google Cloud project.

3. Не создавать новую папку на Google Drive.

4. Не менять ссылки в `knowledge_base`, если текущие открываются.

5. Не удалять таблицу `documents_ai`.

6. Не удалять backup workflow.

7. Не возвращать `Supabase account` на старый `*.supabase.co`.

8. Не возвращать OpenAI-узлы на старый `OpenAI account`.

9. Не публиковать workflow, пока `documents_ai` пустая.

## Безопасность

Секреты в этот файл не записаны.

Если какой-то пароль, токен, API-ключ, client secret или service role key случайно попадал на скриншот или в чат, его нужно сменить.
