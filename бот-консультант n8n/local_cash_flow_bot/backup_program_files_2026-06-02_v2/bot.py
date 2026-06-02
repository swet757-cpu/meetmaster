from pathlib import Path


SOURCE = Path(__file__).resolve().parent.parent / "bot.py"

raise RuntimeError(
    "Для восстановления используйте рабочий файл bot.py из родительской папки. "
    f"Источник: {SOURCE}"
)
