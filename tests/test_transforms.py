import pandas as pd
import pytest
from source import transformations as t


@pytest.fixture
def orders():
    return pd.DataFrame({
        "InvoiceNo": ["1001", "C1002", "1003", "1004"],
        "StockCode": ["A", "B", "C", "D"],
        "Description": ["Mug", "Plate", None, "Bowl"],
        "Quantity": [2, -1, 3, 0],
        "InvoiceDate": ["2010-12-01 08:00", "2010-12-01 09:00",
                        "2010-12-01 10:00", "2010-12-02 11:00"],
        "UnitPrice": [2.5, 4.0, 1.0, 5.0],
        "CustomerID": [17850.0, 12345.0, None, 11111.0],
        "Country": ["UK"] * 4,
    })


def test_remove_cancelled(orders):
    assert "C1002" not in t.remove_cancelled(orders)["InvoiceNo"].values


def test_handle_nulls_fills_description(orders):
    out = t.handle_nulls(orders)
    assert out["Description"].isna().sum() == 0


def test_convert_types(orders):
    out = t.convert_types(orders)
    assert pd.api.types.is_datetime64_any_dtype(out["InvoiceDate"])
    assert str(out["CustomerID"].dtype) == "Int64"


def test_remove_invalid_values(orders):
    out = t.remove_invalid_values(t.convert_types(orders))
    assert (out["Quantity"] > 0).all()


def test_add_total_price(orders):
    out = t.add_total_price(t.convert_types(orders))
    assert out.loc[0, "TotalPrice"] == 5.0


def test_daily_sales(orders):
    clean = t.add_total_price(t.remove_invalid_values(t.convert_types(orders)))
    daily = t.daily_sales(clean)
    assert len(daily) == 1
    assert daily.loc[0, "total_sales"] == 8.0   # 2*2.5 + 3*1.0


def test_validate_schema_raises():
    with pytest.raises(ValueError):
        t.validate_schema(pd.DataFrame({"a": [1]}))