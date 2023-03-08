import la_emissions_data

import pytest
import pandas as pd
from pathlib import Path

top_level = Path("__file__").parent.parent


@pytest.fixture()
def df() -> pd.DataFrame:
    return pd.read_csv(
        top_level
        / "data"
        / "packages"
        / "uk_local_authority_emissions_data"
        / "local_authority_emissions.csv"
    )


def test_number_of_authorities(df: pd.DataFrame):
    # 409 current authorities as of 01/04/2023
    assert df["local-authority-code"].nunique() == 393
