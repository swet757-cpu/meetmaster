from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd
import xlsxwriter


OSV_SHEET = "OSV"
PL_SHEET = "P_L"
BS_SHEET = "BS"


@dataclass(frozen=True)
class Line:
    name: str
    formula: str
    value: float


@dataclass(frozen=True)
class BalanceLine:
    name: str
    start_formula: str
    start_value: float
    end_formula: str
    end_value: float


def create_statement_workbook(
    osv: pd.DataFrame,
    output_dir: Path,
    user_id: int,
    mapping: pd.DataFrame | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"financial_report_{user_id}_{timestamp}.xlsx"

    workbook = xlsxwriter.Workbook(output_path)
    formats = _formats(workbook)
    _write_osv(workbook, osv, formats)
    _write_pl(workbook, osv, mapping, formats)
    _write_bs(workbook, osv, formats)
    workbook.close()
    return output_path


def _write_osv(workbook: xlsxwriter.Workbook, osv: pd.DataFrame, formats: dict[str, xlsxwriter.format.Format]) -> None:
    sheet = workbook.add_worksheet(OSV_SHEET)
    columns = ["Счет", "НачДт", "НачКт", "ОборотДт", "ОборотКт", "КонДт", "КонКт"]
    for col_idx, column in enumerate(columns):
        sheet.write(0, col_idx, column, formats["header"])

    for row_idx, (_, row) in enumerate(osv.iterrows(), start=1):
        sheet.write(row_idx, 0, str(row.get("Счет", "")))
        for col_idx, column in enumerate(columns[1:], start=1):
            sheet.write_number(row_idx, col_idx, _number(row.get(column, 0)), formats["money"])

    sheet.set_column(0, 0, 16)
    sheet.set_column(1, 6, 16)


def _write_pl(
    workbook: xlsxwriter.Workbook,
    osv: pd.DataFrame,
    mapping: pd.DataFrame | None,
    formats: dict[str, xlsxwriter.format.Format],
) -> None:
    sheet = workbook.add_worksheet(PL_SHEET)
    sheet.write(0, 0, "P_L", formats["header"])
    sheet.write(0, 1, "Сумма", formats["header"])

    lines = _pl_lines(osv, mapping)
    for row_idx, line in enumerate(lines, start=1):
        sheet.write(row_idx, 0, line.name)
        sheet.write_formula(row_idx, 1, line.formula, formats["money"], line.value)

    total_row = len(lines) + 1
    total_value = sum(line.value for line in lines)
    sheet.write(total_row, 0, "Финансовый результат", formats["total"])
    sheet.write_formula(total_row, 1, f"=SUM(B2:B{total_row})", formats["total_money"], total_value)

    sheet.set_column(0, 0, 30)
    sheet.set_column(1, 1, 18)


def _write_bs(workbook: xlsxwriter.Workbook, osv: pd.DataFrame, formats: dict[str, xlsxwriter.format.Format]) -> None:
    sheet = workbook.add_worksheet(BS_SHEET)
    sheet.write(0, 0, "BS", formats["header"])
    sheet.write(0, 1, "Начало", formats["header"])
    sheet.write(0, 2, "Конец", formats["header"])

    lines = _bs_lines(osv)
    total_names = {
        "Оборотные активы",
        "Активы всего",
        "Краткосрочные обязательства",
        "Пассивы всего",
        "Чистый оборотный капитал",
        "Стоимость компании",
    }

    for row_idx, line in enumerate(lines, start=1):
        is_total = line.name in total_names
        name_format = formats["total"] if is_total else None
        money_format = formats["total_money"] if is_total else formats["money"]
        sheet.write(row_idx, 0, line.name, name_format)
        sheet.write_formula(row_idx, 1, line.start_formula, money_format, line.start_value)
        sheet.write_formula(row_idx, 2, line.end_formula, money_format, line.end_value)

    sheet.set_column(0, 0, 30)
    sheet.set_column(1, 2, 18)


def _pl_lines(osv: pd.DataFrame, mapping: pd.DataFrame | None) -> list[Line]:
    if mapping is not None and not mapping.empty:
        return _pl_from_mapping(osv, mapping)

    fallback = [
        ("Выручка", [("90.01", "ОборотКт", 1), ("90.03", "ОборотДт", -1)]),
        ("Себестоимость", [("90.02", "ОборотДт", -1)]),
        ("Коммерческие расходы", [("44", "ОборотДт", -1)]),
        ("Общехозяйственные расходы", [("26", "ОборотДт", -1)]),
        ("Прочие доходы", [("91.01", "ОборотКт", 1)]),
        ("Прочие расходы", [("91.02", "ОборотДт", -1)]),
        ("Налог на прибыль", [("68.04", "ОборотКт", 1), ("99.02", "ОборотКт", 1)]),
    ]
    return [_line_from_parts(osv, name, parts) for name, parts in fallback]


def _pl_from_mapping(osv: pd.DataFrame, mapping: pd.DataFrame) -> list[Line]:
    labels = {
        "Коммерческие": "Коммерческие расходы",
        "Общехозяйственные": "Общехозяйственные расходы",
    }
    order = [
        "Выручка",
        "Себестоимость",
        "Коммерческие расходы",
        "Общехозяйственные расходы",
        "Прочие доходы",
        "Прочие расходы",
        "Налог на прибыль",
    ]
    grouped: dict[str, list[tuple[str, str, float]]] = {}
    active = mapping[mapping["Активно"].fillna(0).astype(float) == 1]
    for _, row in active.iterrows():
        name = labels.get(str(row["Статья"]).strip(), str(row["Статья"]).strip())
        grouped.setdefault(name, []).append(
            (str(row["Счет mask"]).strip(), str(row["Источник"]).strip(), float(row["Знак"]))
        )

    lines = [_line_from_parts(osv, name, grouped.get(name, [])) for name in order]
    if not grouped.get("Налог на прибыль"):
        lines[6] = _line_from_parts(osv, "Налог на прибыль", [("68.04", "ОборотКт", -1)])
    extra_names = [name for name in grouped if name not in order]
    lines.extend(_line_from_parts(osv, name, grouped[name]) for name in extra_names)
    return lines


def _line_from_parts(osv: pd.DataFrame, name: str, parts: list[tuple[str, str, float]]) -> Line:
    if not parts:
        return Line(name=name, formula="=0", value=0.0)
    formulas = []
    value = 0.0
    for account, source, sign in parts:
        formulas.append(f"{_source_formula(account, source)}*{sign:g}")
        value += _source_value(osv, account, source) * sign
    return Line(name=name, formula="=" + "+".join(formulas), value=value)


def _bs_lines(osv: pd.DataFrame) -> list[BalanceLine]:
    lines = [
        _asset_line(osv, "Деньги", ["50", "51", "52", "55", "57"]),
        _asset_line(osv, "Финансовые вложения", ["58"]),
        _asset_line(osv, "Запасы", ["10", "41"]),
        _asset_line(osv, "ДЗ", ["60.02", "62.01", "76.09"]),
    ]
    lines.append(_sum_line("Оборотные активы", lines))

    fixed_assets = _liability_line(osv, "Основные средства", ["02"], negative=True)
    lines.append(fixed_assets)
    lines.append(_manual_sum_line("Активы всего", [lines[4], fixed_assets], "B6+B7", "C6+C7"))

    liabilities = [
        _liability_line(osv, "КЗ", ["60.01", "62.02", "76.05"]),
        _liability_line(osv, "Кредиты и займы", ["66", "67"]),
        _liability_line(osv, "Налоги и взносы", ["68", "69"]),
        _liability_line(osv, "Зарплата", ["70"]),
        _liability_line(osv, "Подотчетные лица", ["71"]),
    ]
    lines.extend(liabilities)
    short_liabilities = _manual_sum_line("Краткосрочные обязательства", liabilities, "SUM(B9:B13)", "SUM(C9:C13)")
    lines.append(short_liabilities)

    equity = [
        _liability_line(osv, "Капитал", ["80"]),
        _liability_line(osv, "Нераспределенная прибыль", ["84"]),
    ]
    lines.extend(equity)
    total_liabilities = _manual_sum_line("Пассивы всего", [short_liabilities, *equity], "SUM(B14:B16)", "SUM(C14:C16)")
    lines.append(total_liabilities)

    current_assets = lines[4]
    total_assets = lines[6]
    nwc = BalanceLine(
        name="Чистый оборотный капитал",
        start_formula="=B6-B14",
        start_value=current_assets.start_value - short_liabilities.start_value,
        end_formula="=C6-C14",
        end_value=current_assets.end_value - short_liabilities.end_value,
    )
    lines.append(nwc)
    lines.append(
        BalanceLine(
            name="Стоимость компании",
            start_formula="=B8-B17",
            start_value=total_assets.start_value - total_liabilities.start_value,
            end_formula="=C8-C17",
            end_value=total_assets.end_value - total_liabilities.end_value,
        )
    )
    return lines


def _asset_line(osv: pd.DataFrame, name: str, accounts: list[str]) -> BalanceLine:
    return BalanceLine(
        name=name,
        start_formula="=" + "+".join(_balance_formula(account, "НачДт", "НачКт") for account in accounts),
        start_value=sum(_balance_value(osv, account, "НачДт", "НачКт") for account in accounts),
        end_formula="=" + "+".join(_balance_formula(account, "КонДт", "КонКт") for account in accounts),
        end_value=sum(_balance_value(osv, account, "КонДт", "КонКт") for account in accounts),
    )


def _liability_line(osv: pd.DataFrame, name: str, accounts: list[str], *, negative: bool = False) -> BalanceLine:
    sign = -1 if negative else 1
    start_value = sum(_balance_value(osv, account, "НачКт", "НачДт") for account in accounts) * sign
    end_value = sum(_balance_value(osv, account, "КонКт", "КонДт") for account in accounts) * sign
    if not negative:
        start_value = max(0.0, start_value)
        end_value = max(0.0, end_value)

    return BalanceLine(
        name=name,
        start_formula=_liability_formula(accounts, "НачКт", "НачДт", sign, negative),
        start_value=start_value,
        end_formula=_liability_formula(accounts, "КонКт", "КонДт", sign, negative),
        end_value=end_value,
    )


def _liability_formula(accounts: list[str], plus_column: str, minus_column: str, sign: int, negative: bool) -> str:
    formula = "+".join(f"({_balance_formula(account, plus_column, minus_column)})*{sign}" for account in accounts)
    if negative:
        return f"={formula}"
    return f"=MAX(0,{formula})"


def _sum_line(name: str, lines: list[BalanceLine]) -> BalanceLine:
    return _manual_sum_line(name, lines, "SUM(B2:B5)", "SUM(C2:C5)")


def _manual_sum_line(name: str, lines: list[BalanceLine], start_formula: str, end_formula: str) -> BalanceLine:
    return BalanceLine(
        name=name,
        start_formula=f"={start_formula}",
        start_value=sum(line.start_value for line in lines),
        end_formula=f"={end_formula}",
        end_value=sum(line.end_value for line in lines),
    )


def _source_formula(account: str, source: str) -> str:
    column = _source_column(source)
    return f'SUMIF({OSV_SHEET}!$A:$A,"{account}",{OSV_SHEET}!${column}:${column})'


def _source_value(osv: pd.DataFrame, account: str, source: str) -> float:
    return float(_account_rows(osv, account)[source].fillna(0).sum())


def _balance_formula(account: str, plus_column: str, minus_column: str) -> str:
    plus = _source_formula(account, plus_column)
    minus = _source_formula(account, minus_column)
    return f"({plus}-{minus})"


def _balance_value(osv: pd.DataFrame, account: str, plus_column: str, minus_column: str) -> float:
    rows = _account_rows(osv, account)
    return float(rows[plus_column].fillna(0).sum() - rows[minus_column].fillna(0).sum())


def _account_rows(osv: pd.DataFrame, account: str) -> pd.DataFrame:
    exact = osv[osv["Счет"].astype(str).str.strip() == account]
    if not exact.empty:
        return exact
    return osv[osv["Счет"].astype(str).str.startswith(f"{account}.")]


def _source_column(source: str) -> str:
    columns = {
        "НачДт": "B",
        "НачКт": "C",
        "ОборотДт": "D",
        "ОборотКт": "E",
        "КонДт": "F",
        "КонКт": "G",
    }
    return columns[source]


def _formats(workbook: xlsxwriter.Workbook) -> dict[str, xlsxwriter.format.Format]:
    return {
        "header": workbook.add_format({"bold": True, "bg_color": "#D9EAF7"}),
        "money": workbook.add_format({"num_format": '# ##0.00;[Red]-# ##0.00;0.00'}),
        "total": workbook.add_format({"bold": True}),
        "total_money": workbook.add_format({"bold": True, "num_format": '# ##0.00;[Red]-# ##0.00;0.00'}),
    }


def _number(value: object) -> float:
    if pd.isna(value):
        return 0.0
    return float(value)
