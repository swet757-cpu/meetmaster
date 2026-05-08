$ErrorActionPreference = 'Stop'

$targetPath = Join-Path $PSScriptRoot '..\Инструкция как создать бота в телеграмм.docx'
$targetPath = [System.IO.Path]::GetFullPath($targetPath)

$title = 'Инструкция как создать бота в телеграмм'
$lines = @(
    'Инструкция как создать бота в Telegram на базе n8n',
    '',
    '1. Что это за бот',
    'Это Telegram-бот Cash Flow Lifesaver. Он помогает пользователю выбрать один из трёх сценариев: кассовый разрыв, прибыль есть, а денег нет, или обучение планированию. Бот работает через n8n, отвечает в Telegram, использует Google Drive для материалов и Supabase для базы знаний.',
    '',
    '2. Какие программы и сервисы использовались',
    '1) Telegram и BotFather — для создания бота и получения токена.',
    '2) n8n на сервере https://n8n1.sweevottak.pro — для всей логики сценариев.',
    '3) Google Drive и Google Cloud Console — для хранения файлов, OAuth и триггеров по папке.',
    '4) Supabase на своём сервере https://supabase2.sweevottak.pro — для таблиц knowledge_base и documents_ai.',
    '5) ProxyAPI — как OpenAI-совместимый провайдер для chat/completions, embeddings и расшифровки.',
    '6) VS Code — для локальных файлов, заметок и проверки структуры проекта.',
    '7) Docker и PostgreSQL на сервере — для правок n8n и диагностики.',
    '',
    '3. Какие локальные файлы использовались',
    '1) assets\checklist_cash_gap.pdf',
    '2) assets\profit_vs_cash_guide.pdf',
    '3) assets\kb_cash_flow_lifesaver.txt',
    '4) rabota_na_zavtra.md — журнал, что сделано и что проверять дальше.',
    '',
    '4. Какая папка и какие материалы использовались на Google Drive',
    'Рабочая папка на Google Drive: Мой Спасатель.',
    'Использовались ссылки:',
    '1) emergency -> https://drive.google.com/file/d/1Ui_lXPZqy6x7wiX__ASeZUCkHJqFt4Il/view?usp=drive_link',
    '2) profit_vs_cash -> https://drive.google.com/file/d/1FH8axlGXvUMtMXyrCwgFtfPyNNs0UP8n/view?usp=drive_link',
    '3) calendar -> https://docs.google.com/spreadsheets/d/1Udx77aRfCAn0kGeKyT95B_hPf3rDDleoH9-CfBIuwAU/edit?usp=sharing',
    'Папка для отслеживания в триггерах Google Drive: folder id 1ZLK0_M4RP0eNB0-p3BSKiNnMBuxnyY9G.',
    '',
    '5. В каком порядке всё настраивалось',
    'Шаг 1. Прочитана логика бота из локальных файлов и старой схемы.',
    'Шаг 2. Проверены и собраны материалы в папке assets.',
    'Шаг 3. Подключён Telegram-бот к n8n через узел Telegram Trigger и узел отправки сообщений.',
    'Шаг 4. Подключён Google Drive account через OAuth и настроены узлы File Created и File Updated.',
    'Шаг 5. В Google Cloud Console включён Google Drive API, настроен OAuth client и test user.',
    'Шаг 6. Настроен self-hosted Supabase account. Старый credential смотрел в облачный *.supabase.co и был заменён на https://supabase2.sweevottak.pro.',
    'Шаг 7. В Supabase созданы и проверены таблица documents_ai и функция match_documents_ai.',
    'Шаг 8. В таблицу knowledge_base внесены ссылки на PDF и Google Таблицу.',
    'Шаг 9. Настроен AI Agent: системный промпт, сценарии и ссылки на базу знаний.',
    'Шаг 10. Настроен OpenAI-совместимый credential через ProxyAPI.',
    'Шаг 11. Исправлены блокеры публикации workflow.',
    'Шаг 12. Workflow опубликован и переведён в active = true.',
    'Шаг 13. Проверен живой ответ бота в Telegram.',
    '',
    '6. Что именно подключалось в n8n',
    '1) Credential Google Drive account — для доступа к папке Мой Спасатель.',
    '2) Credential Supabase account — для сервера https://supabase2.sweevottak.pro.',
    '3) Credential OpenAI account 2 — для ProxyAPI.',
    '',
    'Для OpenAI account 2 использовались параметры:',
    'API Key = ключ ProxyAPI',
    'Organization ID = пусто',
    'Base URL = https://api.proxyapi.ru/openai/v1',
    '',
    'На этот credential были переведены узлы:',
    '1) OpenAI Chat Model',
    '2) Embeddings OpenAI',
    '3) Embeddings OpenAI1',
    '4) Transcribe a recording',
    '',
    '7. Какие узлы и ветки есть в схеме',
    'Верхняя ветка: Telegram Trigger -> Switch -> обработка текста или аудио -> AI Agent -> Send a text message.',
    'Нижняя ветка: File Created / File Updated -> Loop Over Items -> Edit Fields3 -> Delete Old Docs -> Download File -> Insert into Supabase Vectorstore.',
    '',
    '8. Какие таблицы и объекты базы были нужны',
    '1) knowledge_base — короткая база с триггерами и ссылками.',
    '2) documents_ai — таблица для документов и embeddings.',
    '3) match_documents_ai — функция поиска для vector store.',
    '',
    '9. Какие ошибки были найдены и как исправлялись',
    'Ошибка 1. Google OAuth callback state invalid / client authentication failed.',
    'Причина: OAuth в Google Cloud был настроен не до конца, тестовый пользователь не добавлен, а клиентские данные путались с service account.',
    'Исправление: создан OAuth client для web application, добавлен redirect URI n8n, добавлен test user и заново подключён Google Drive account.',
    '',
    'Ошибка 2. Supabase documents_ai not found.',
    'Причина: n8n смотрел в старый Supabase credential, который указывал на чужой или старый проект.',
    'Исправление: credential Supabase account переведён на https://supabase2.sweevottak.pro, обновлён cache schema, перезапущен supabase-rest, выданы права на таблицу и функцию.',
    '',
    'Ошибка 3. Workflow не публиковался.',
    'Причина: в схеме оставался Postgres Chat Memory без credentials, а OpenAI Chat Model не имел модели.',
    'Исправление: проблемный узел памяти удалён, в OpenAI Chat Model поставлена модель gpt-4o-mini, исправления внесены и в текущую схему, и в автосохранённый черновик.',
    '',
    'Ошибка 4. Бот перестал отвечать в Telegram.',
    'Причина: Telegram message node пытался разбирать текст как markdown, а ссылки и символы подчёркивания ломали parse entities.',
    'Исправление: в узле Send a text message1 установлен parse_mode = HTML. После этого n8n был перезапущен.',
    '',
    'Ошибка 5. Ответы выглядели некрасиво: ###, markdown, лишние символы.',
    'Причина: системный промпт разрешал markdown-стиль ответа.',
    'Исправление: в AI Agent добавлено правило отвечать чистым текстом, без ###, без markdown-заголовков, со ссылками как обычным URL.',
    '',
    'Ошибка 6. Embeddings падали с 429 quota exceeded.',
    'Причина: сначала использовался обычный OpenAI API без доступной квоты. Потом часть узлов перевели на ProxyAPI.',
    'Статус: это отдельная ветка для доработки. На работу Telegram-бота она не мешает.',
    '',
    '10. Что уже работает',
    '1) Workflow опубликован.',
    '2) Статус workflow active = true.',
    '3) Telegram Trigger принимает сообщения.',
    '4) Бот отвечает в Telegram.',
    '5) Google Drive account подключён.',
    '6) knowledge_base заполнена тремя ссылками.',
    '',
    '11. Что ещё нужно проверять отдельно',
    '1) Добить нижнюю ветку загрузки документов в documents_ai.',
    '2) Ещё раз прогнать Insert into Supabase Vectorstore после окончательной проверки ProxyAPI embeddings.',
    '3) Проверить, что новые файлы из папки Мой Спасатель действительно попадают в documents_ai.',
    '',
    '12. Как повторить создание такого бота в новом проекте',
    '1) Сначала собрать логику сценариев и материалы.',
    '2) Создать Telegram-бота и получить токен.',
    '3) Поднять n8n и сразу собрать верхнюю ветку Telegram, чтобы бот начал отвечать как можно раньше.',
    '4) Подключить Google Drive и выбрать одну рабочую папку.',
    '5) Подключить Supabase и заранее создать таблицы и функцию поиска.',
    '6) Только после этого подключать embeddings и vector store.',
    '7) Перед публикацией убрать все узлы без credentials и все пустые обязательные поля.',
    '',
    '13. Что нельзя забывать',
    '1) Не путать OAuth client и service account в Google Cloud.',
    '2) Не путать старый облачный Supabase и self-hosted Supabase.',
    '3) Для ProxyAPI в n8n важен именно Base URL https://api.proxyapi.ru/openai/v1.',
    '4) Для Telegram-узла нужно parse_mode, а не parseMode.',
    '5) Перед правками в рабочем workflow лучше сделать резервную копию.',
    '',
    '14. Какие серверные инструменты использовались при исправлениях',
    '1) SSH на сервер.',
    '2) Docker container n8n.',
    '3) Docker container n8n-postgres.',
    '4) Docker container supabase-rest.',
    '5) PostgreSQL через psql для проверки workflow_entity, workflow_history и таблиц Supabase.',
    '',
    '15. Итог',
    'Бот в Telegram запущен и отвечает. Основной рабочий контур — Telegram + AI Agent + ссылки из knowledge_base — уже работает. Отдельно потом нужно закончить автоматическую загрузку файлов в documents_ai через нижнюю ветку.'
)

function Escape-XmlText([string]$text) {
    return [System.Security.SecurityElement]::Escape($text)
}

function New-ParagraphXml([string]$text) {
    if ([string]::IsNullOrEmpty($text)) {
        return '<w:p/>'
    }
    $escaped = Escape-XmlText $text
    return "<w:p><w:r><w:t xml:space=`"preserve`">$escaped</w:t></w:r></w:p>"
}

$paragraphXml = ($lines | ForEach-Object { New-ParagraphXml $_ }) -join "`n"
$created = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

$contentTypes = @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
'@

$rels = @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
'@

$core = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>$([System.Security.SecurityElement]::Escape($title))</dc:title>
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">$created</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">$created</dcterms:modified>
</cp:coreProperties>
"@

$app = @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex</Application>
</Properties>
'@

$document = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:wne="http://schemas.microsoft.com/office/2006/relationships" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" mc:Ignorable="w14 wp14">
  <w:body>
$paragraphXml
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>
      <w:cols w:space="708"/>
      <w:docGrid w:linePitch="360"/>
    </w:sectPr>
  </w:body>
</w:document>
"@

$docRels = @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>
'@

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

if (Test-Path $targetPath) {
    Remove-Item -LiteralPath $targetPath -Force
}

$fileStream = [System.IO.File]::Open($targetPath, [System.IO.FileMode]::CreateNew)
try {
    $archive = New-Object System.IO.Compression.ZipArchive($fileStream, [System.IO.Compression.ZipArchiveMode]::Create, $false)
    try {
        $entries = [ordered]@{
            '[Content_Types].xml'        = $contentTypes
            '_rels/.rels'                = $rels
            'docProps/core.xml'          = $core
            'docProps/app.xml'           = $app
            'word/document.xml'          = $document
            'word/_rels/document.xml.rels' = $docRels
        }

        foreach ($path in $entries.Keys) {
            $entry = $archive.CreateEntry($path)
            $writer = New-Object System.IO.StreamWriter($entry.Open(), [System.Text.UTF8Encoding]::new($false))
            try {
                $writer.Write($entries[$path])
            }
            finally {
                $writer.Dispose()
            }
        }
    }
    finally {
        $archive.Dispose()
    }
}
finally {
    $fileStream.Dispose()
}

Get-Item -LiteralPath $targetPath | Select-Object FullName, Length, LastWriteTime
