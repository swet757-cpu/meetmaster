from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class CorrectionResult:
    mapping: pd.DataFrame
    changed: bool


def build_report(osv: pd.DataFrame, mapping: pd.DataFrame) -> str:
    account20 = _account_rows(osv, "20")
    debit_turnover_20 = _sum(account20["ОборотДт"])
    closing_debit_20 = _sum(account20["КонДт"])

    alerts: list[str] = []
    facts = [
        "Результат проверки:",
        f"Счет 20, оборот Дт: {_money(debit_turnover_20)} руб.",
        f"Счет 20, конечное сальдо Дт: {_money(closing_debit_20)} руб.",
    ]

    if account20.empty:
        alerts.append("данных по счету 20 нет.")

    if closing_debit_20 > 0:
        alerts.append(
            "риск - на 20 счете висит остаток. Проверьте наличие незавершенного производства, иначе месяц не закрыт."
        )

    if debit_turnover_20 > 0:
        row20 = _mapping_rows(mapping, "20")
        if row20.empty:
            alerts.append("системная ошибка - движение по 20 счету есть, но в маппинге нет строки со счетом 20.")
        elif (row20["Активно"].fillna(0).astype(float) == 0).any():
            alerts.append(
                "системная ошибка - движение по 20 счету есть, но в маппинге он отключен. Себестоимость не соберется."
            )

    negative_balance = osv[(osv["КонДт"].fillna(0) < 0) | (osv["КонКт"].fillna(0) < 0)]
    if not negative_balance.empty:
        accounts = ", ".join(negative_balance["Счет"].head(10).astype(str).tolist())
        alerts.append(f"аномалия - есть отрицательное конечное сальдо: {accounts}.")

    if alerts:
        return "\n".join(facts + ["", "Алерты:"] + [f"- {alert}" for alert in alerts])

    return "\n".join(facts + ["", "Алертов нет."])


def correct_mapping(osv: pd.DataFrame, mapping: pd.DataFrame) -> CorrectionResult:
    account20 = _account_rows(osv, "20")
    debit_turnover_20 = _sum(account20["ОборотДт"])

    corrected = mapping.copy()
    if debit_turnover_20 <= 0:
        return CorrectionResult(mapping=corrected, changed=False)

    changed = False
    mask20 = corrected["Счет mask"].astype(str).str.strip() == "20"
    mask9002 = corrected["Счет mask"].astype(str).str.strip() == "90.02"

    if mask20.any():
        changed = changed or not (corrected.loc[mask20, "Активно"].astype(float) == 1.0).all()
        corrected.loc[mask20, "Активно"] = 1.0

    if mask9002.any():
        changed = changed or not (corrected.loc[mask9002, "Активно"].astype(float) == 0.0).all()
        corrected.loc[mask9002, "Активно"] = 0.0

    return CorrectionResult(mapping=corrected, changed=changed)


def _account_rows(df: pd.DataFrame, account: str) -> pd.DataFrame:
    exact = df[df["Счет"].astype(str).str.strip() == account]
    if not exact.empty:
        return exact
    return df[df["Счет"].astype(str).str.startswith(account)]


def _mapping_rows(df: pd.DataFrame, account: str) -> pd.DataFrame:
    return df[df["Счет mask"].astype(str).str.strip() == account]


def _sum(series: pd.Series) -> float:
    return float(series.fillna(0).sum())


def _money(value: float) -> str:
    return f"{value:,.2f}".replace(",", " ").replace(".", ",")
