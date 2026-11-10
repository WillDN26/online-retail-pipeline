import logging
import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"InvoiceNo", "StockCode", "Description", "Quantity",
                    "InvoiceDate", "UnitPrice", "CustomerID", "Country"}

COLUMN_RENAMES = {
    "Invoice": "InvoiceNo",
    "Price": "UnitPrice",
    "Customer ID": "CustomerID",
}

def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns=COLUMN_RENAMES)

def validate_schema(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Input is missing required columns: {sorted(missing)}")


def remove_cancelled(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["InvoiceNo"].astype(str).str.startswith("C")
    logger.info("Removing %d cancelled order rows", mask.sum())
    return df[~mask].copy()


def handle_nulls(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.dropna(subset=["InvoiceNo", "InvoiceDate", "Quantity", "UnitPrice"]).copy()
    df["Description"] = df["Description"].fillna("UNKNOWN")
    logger.info("Dropped %d rows with nulls in key columns", before - len(df))
    logger.info("%d rows have no CustomerID (kept)", df["CustomerID"].isna().sum())
    return df


def convert_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["InvoiceNo"] = df["InvoiceNo"].astype(str)
    df["StockCode"] = df["StockCode"].astype(str)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["CustomerID"] = df["CustomerID"].astype("Int64")
    bad = df[["InvoiceDate", "Quantity", "UnitPrice"]].isna().any(axis=1).sum()
    if bad:
        logger.warning("%d rows failed type conversion and will be dropped", bad)
    return df.dropna(subset=["InvoiceDate", "Quantity", "UnitPrice"])


def remove_invalid_values(df: pd.DataFrame) -> pd.DataFrame:
    mask = (df["Quantity"] > 0) & (df["UnitPrice"] > 0)
    logger.info("Removing %d rows with non-positive quantity/price", (~mask).sum())
    return df[mask].copy()


def add_total_price(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["TotalPrice"] = df["Quantity"] * df["UnitPrice"]
    return df


def daily_sales(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.assign(SaleDate=df["InvoiceDate"].dt.normalize())
          .groupby("SaleDate", as_index=False)
          .agg(total_sales=("TotalPrice", "sum"),
               orders=("InvoiceNo", "nunique"),
               units_sold=("Quantity", "sum"))
    )
    out["total_sales"] = out["total_sales"].round(2)
    return out