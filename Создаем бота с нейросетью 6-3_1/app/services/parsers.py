from dataclasses import dataclass
from pathlib import Path

import pandas as pd


OSV_COLUMNS = [
    "Счет_и_наименование",
    "НачДт",
    "НачКт",
    "ОборотДт",
    "ОборотКт",
    "КонДт",
    "КонКт",
]

MAPPING_COLUMNS = ["Активно", "Статья", "Счет mask", "Источник", "Знак", "Сумма"]


@dataclass(frozen=True)
class MappingLayout:
    vertical_header: bool
    extension: str


def parse_osv(path: Path) -> pd.DataFrame:
    raw = _read_raw_table(path)
    data_start = _find_osv_data_start(raw)
    df = raw.iloc[data_start:, :7].copy()
    df.columns = OSV_COLUMNS
    df = df.dropna(how="all")

    df["Счет_и_наименование"] = df["Счет_и_наименование"].astype(str).str.strip()
    df = df[df["Счет_и_наименование"].ne("")]
    df = df[~df["Счет_и_наименование"].str.lower().eq("nan")]
    df["Счет"] = df["Счет_и_наименование"].str.split(",", n=1).str[0].str.strip()
    df = df[~df["Счет"].str.lower().eq("итого")]

    for column in ["НачДт", "НачКт", "ОборотДт", "ОборотКт", "КонДт", "КонКт"]:
        df[column] = _to_number(df[column])

    return df.reset_index(drop=True)


def parse_mapping(path: Path) -> pd.DataFrame:
    raw = _read_raw_table(path)
    raw = _ensure_min_columns(raw, len(MAPPING_COLUMNS))
    layout = _detect_mapping_layout(raw, path)

    if layout.vertical_header:
        df = raw.iloc[len(MAPPING_COLUMNS) :, : len(MAPPING_COLUMNS)].copy()
        df.columns = MAPPING_COLUMNS
    else:
        header_row = _find_horizontal_mapping_header(raw)
        if header_row is not None:
            df = raw.iloc[header_row + 1 :, : len(MAPPING_COLUMNS)].copy()
            df.columns = [str(v).strip() for v in raw.iloc[header_row, : len(MAPPING_COLUMNS)].tolist()]
            df = df.rename(columns=_mapping_column_aliases())
            df = df[MAPPING_COLUMNS]
        else:
            df = raw.iloc[:, : len(MAPPING_COLUMNS)].copy()
            df.columns = MAPPING_COLUMNS

    df = df.dropna(how="all")
    df["Счет mask"] = df["Счет mask"].astype(str).str.strip()
    df = df[df["Счет mask"].ne("")]
    df = df[~df["Счет mask"].str.lower().eq("nan")]
    df["Активно"] = _to_number(df["Активно"]).fillna(0)
    df["Знак"] = _to_number(df["Знак"]).fillna(1)
    df["Сумма"] = _to_number(df["Сумма"])
    df.attrs["layout"] = layout
    return df.reset_index(drop=True)


def _ensure_min_columns(df: pd.DataFrame, min_columns: int) -> pd.DataFrame:
    if df.shape[1] >= min_columns:
        return df

    expanded = df.copy()
    for column in range(df.shape[1], min_columns):
        expanded[column] = None
    return expanded


def save_mapping_copy(mapping: pd.DataFrame, source_path: Path, layout: MappingLayout | None = None) -> Path:
    if layout is None:
        layout = mapping.attrs.get("layout")
    if layout is None:
        layout = MappingLayout(vertical_header=False, extension=source_path.suffix.lower())

    suffix = ".xlsx" if source_path.suffix.lower() == ".xls" else source_path.suffix
    output_path = source_path.with_name(f"{source_path.stem}_v2{suffix}")
    clean = mapping[MAPPING_COLUMNS].copy()

    if layout.vertical_header:
        header = pd.DataFrame([[name] + [None] * (len(MAPPING_COLUMNS) - 1) for name in MAPPING_COLUMNS])
        data = pd.concat([header, clean], ignore_index=True)
        data.columns = list(range(len(MAPPING_COLUMNS)))
        _write_table(data, output_path, header=False)
    else:
        _write_table(clean, output_path, header=True)

    return output_path


def _read_raw_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, sheet_name=0, header=None, dtype=object)

    if suffix == ".csv":
        last_error: Exception | None = None
        for encoding in ("utf-8-sig", "cp1251"):
            try:
                return pd.read_csv(path, header=None, dtype=object, sep=None, engine="python", encoding=encoding)
            except Exception as exc:
                last_error = exc
        raise RuntimeError(f"CSV не прочитан: {last_error}")

    raise RuntimeError(f"Неподдерживаемый формат файла: {suffix}")


def _write_table(df: pd.DataFrame, output_path: Path, header: bool) -> None:
    suffix = output_path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        df.to_excel(output_path, index=False, header=header)
        return
    if suffix == ".csv":
        df.to_csv(output_path, index=False, header=header, sep=";", encoding="utf-8-sig")
        return
    raise RuntimeError(f"Неподдерживаемый формат файла: {suffix}")


def _find_osv_data_start(raw: pd.DataFrame) -> int:
    for idx in range(min(len(raw), 30)):
        first_cell = _cell(raw.iat[idx, 0]).lower()
        row_text = " ".join(_cell(v).lower() for v in raw.iloc[idx].tolist())
        if "счет" in first_cell and "сальдо" in row_text:
            return idx + 2
        if "счет" in row_text and ("оборотдт" in row_text or "кон.дт" in row_text or "конечное" in row_text):
            return idx + 1
    return 7


def _detect_mapping_layout(raw: pd.DataFrame, path: Path) -> MappingLayout:
    first_col = [_cell(v).lower() for v in raw.iloc[: len(MAPPING_COLUMNS), 0].tolist()]
    expected = [name.lower() for name in MAPPING_COLUMNS]
    return MappingLayout(vertical_header=first_col == expected, extension=path.suffix.lower())


def _find_horizontal_mapping_header(raw: pd.DataFrame) -> int | None:
    required = {"активно", "статья", "счет mask"}
    for idx in range(min(len(raw), 15)):
        values = {_cell(v).lower() for v in raw.iloc[idx].tolist()}
        if required.issubset(values):
            return idx
    return None


def _mapping_column_aliases() -> dict[str, str]:
    return {
        "Активно": "Активно",
        "Статья": "Статья",
        "Счет mask": "Счет mask",
        "Счёт mask": "Счет mask",
        "Источник": "Источник",
        "Знак": "Знак",
        "Сумма": "Сумма",
    }


def _to_number(series: pd.Series) -> pd.Series:
    normalized = (
        series.astype(str)
        .str.replace("\u00a0", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.replace("−", "-", regex=False)
    )
    normalized = normalized.mask(normalized.str.lower().isin({"", "nan", "none"}))
    return pd.to_numeric(normalized, errors="coerce")


def _cell(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()
