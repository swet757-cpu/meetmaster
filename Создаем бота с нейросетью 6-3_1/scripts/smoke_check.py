import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.audit import build_report, correct_mapping


def main() -> None:
    osv = pd.DataFrame(
        [
            {
                "Счет": "20",
                "ОборотДт": 1000.0,
                "КонДт": 250.0,
                "КонКт": 0.0,
            },
            {
                "Счет": "90.02",
                "ОборотДт": 1000.0,
                "КонДт": 0.0,
                "КонКт": 0.0,
            },
        ]
    )
    mapping = pd.DataFrame(
        [
            {"Активно": 0.0, "Статья": "Себестоимость", "Счет mask": "20", "Источник": "ОборотДт", "Знак": -1.0, "Сумма": 0.0},
            {"Активно": 1.0, "Статья": "Себестоимость", "Счет mask": "90.02", "Источник": "ОборотДт", "Знак": -1.0, "Сумма": -1000.0},
        ]
    )

    report = build_report(osv, mapping)
    corrected = correct_mapping(osv, mapping)

    assert "системная ошибка" in report
    assert corrected.changed
    assert corrected.mapping.loc[corrected.mapping["Счет mask"] == "20", "Активно"].iloc[0] == 1.0
    assert corrected.mapping.loc[corrected.mapping["Счет mask"] == "90.02", "Активно"].iloc[0] == 0.0

    print("Smoke-check прошел.")


if __name__ == "__main__":
    main()
