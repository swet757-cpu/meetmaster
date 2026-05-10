import logging
from datetime import datetime
from pathlib import Path

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message, ReplyKeyboardRemove

from app.config import get_settings
from app.keyboards import AUDIT_MODE, AUTOCORRECT_MODE, CANCEL, mode_keyboard
from app.states import AuditFlow
from app.services.ai import analyze_osv_with_ai
from app.services.audit import build_report, correct_mapping
from app.services.parsers import parse_mapping, parse_osv, save_mapping_copy
from app.services.statements import create_statement_workbook

router = Router()
logger = logging.getLogger(__name__)
APP_VERSION = "2026-05-10.2"


@router.message(F.text.lower() == "ping")
async def ping(message: Message) -> None:
    await message.answer("pong")


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AuditFlow.waiting_mode)
    await message.answer(
        f"Выберите режим проверки ОСВ и маппинга P&L.\nВерсия: {APP_VERSION}",
        reply_markup=mode_keyboard,
    )


@router.message(F.text == CANCEL)
async def cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Диалог сброшен.", reply_markup=ReplyKeyboardRemove())


@router.message(AuditFlow.waiting_mode, F.text.in_({AUDIT_MODE, AUTOCORRECT_MODE}))
async def choose_mode(message: Message, state: FSMContext) -> None:
    await state.update_data(mode=message.text)
    await state.set_state(AuditFlow.waiting_osv)
    await message.answer(
        "Пришлите файл ОСВ из 1С: `.xlsx` или `.csv`.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(AuditFlow.waiting_mode)
async def wrong_mode(message: Message) -> None:
    await message.answer("Выберите режим кнопкой: Аудитор или Авто-корректор.")


@router.message(AuditFlow.waiting_osv, F.document)
async def receive_osv(message: Message, state: FSMContext) -> None:
    path = await _download_document(message, "osv")
    if path.suffix.lower() not in {".xlsx", ".xls", ".csv"}:
        await message.answer("Нужен файл ОСВ в формате `.xlsx`, `.xls` или `.csv`.")
        return

    await state.update_data(osv_path=str(path))
    await state.set_state(AuditFlow.waiting_mapping)
    await message.answer("ОСВ получил. Теперь пришлите файл `Маппинг_PL`: `.xlsx` или `.csv`.")


@router.message(AuditFlow.waiting_osv)
async def wait_osv_file(message: Message) -> None:
    await message.answer("Пришлите ОСВ именно файлом, не скриншотом.")


@router.message(AuditFlow.waiting_mapping, F.document)
async def receive_mapping(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    mapping_path = await _download_document(message, "mapping")

    if mapping_path.suffix.lower() not in {".xlsx", ".xls", ".csv"}:
        await message.answer("Нужен маппинг в формате `.xlsx`, `.xls` или `.csv`.")
        return

    try:
        osv = parse_osv(Path(data["osv_path"]))
        mapping = parse_mapping(mapping_path)
        report = build_report(osv, mapping)
    except Exception as exc:
        logger.exception("Не смог разобрать файлы")
        await message.answer(f"Не смог разобрать файлы: {exc}")
        return

    await message.answer(report)

    settings = get_settings()
    statement_path = create_statement_workbook(osv, settings.work_dir, message.from_user.id, mapping)
    await message.answer_document(
        FSInputFile(statement_path),
        caption="Готовый отчет P_L и BS. Суммы стоят формулами Excel, исходная ОСВ не менялась.",
    )

    if settings.openai_api_key:
        await message.answer("Нейросеть анализирует ОСВ и маппинг. Это может занять до минуты.")
    try:
        ai_analysis = await analyze_osv_with_ai(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            base_url=settings.openai_base_url,
            report=report,
            osv=osv,
            mapping=mapping,
        )
    except Exception as exc:
        logger.exception("AI-анализ не выполнен")
        await message.answer(f"Нейросеть сейчас не ответила: {exc}")
    else:
        await message.answer(ai_analysis.text)

    if data.get("mode") == AUTOCORRECT_MODE:
        corrected = correct_mapping(osv, mapping)
        if corrected.changed:
            output_path = save_mapping_copy(corrected.mapping, mapping_path)
            await message.answer_document(
                FSInputFile(output_path),
                caption="Исправленный маппинг сохранен отдельной копией. Исходный файл не менялся.",
            )
        else:
            await message.answer("Авто-корректор ничего не менял: оборота Дт по счету 20 нет.")

    await state.clear()


@router.message(AuditFlow.waiting_mapping)
async def wait_mapping_file(message: Message) -> None:
    await message.answer("Пришлите файл маппинга, не скриншот.")


async def _download_document(message: Message, prefix: str) -> Path:
    settings = get_settings()
    document = message.document
    if document is None:
        raise RuntimeError("Документ не найден.")

    suffix = Path(document.file_name or "").suffix
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{message.from_user.id}_{timestamp}{suffix}"
    path = settings.work_dir / filename

    bot = message.bot
    file = await bot.get_file(document.file_id)
    await bot.download_file(file.file_path, destination=path)
    return path
