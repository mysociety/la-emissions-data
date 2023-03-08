import pandas as pd
import numpy as np
from pathlib import Path
from data_common.dataset import get_dataset_df
from data_common.pandas.df_extensions import la, space
from scipy.stats.mstats import winsorize
from data_common.management.run_notebook import run_notebook
from datetime import date

# deal with councils that existed as of this date
date_for_councils = date(2023, 4, 2)


def get_la_emissions_data_with_population():
    """
    Get local authoritity dataset with population.
    """
    df = (
        pd.read_csv(
            Path(
                "data",
                "packages",
                "uk_local_authority_emissions_data",
                "local_authority_emissions.csv",
            )
        )
        .la.get_council_info(
            ["pop-2020", "area", "lower-or-unitary"], as_of_date=date_for_councils
        )
        .sort_values("pop-2020", ascending=False)
    )
    assert df["pop-2020"].isna().any() == False
    assert df["area"].isna().any() == False
    return df


def get_gdp_df():

    gdp = pd.read_excel(
        str(
            Path(
                "data",
                "raw",
                "external",
                "regionalgrossdomesticproductlocalauthorities.xlsx",
            )
        ),
        sheet_name="Table 5",
        header=1,
    )
    gdp.columns = list(gdp.columns)[:-1] + ["2019"]

    gdp = (
        gdp[["LA code", "2019"]]  # type:ignore
        .loc[lambda df: ~df["LA code"].isna()]
        .la.create_code_column(
            "gss", source_col="LA code", set_index=True, drop_source=True
        )
        .reset_index()
        .la.to_current(as_of_date=date_for_councils)
        .rename(columns={"2019": "gdp"})
    )
    higher_gdp = gdp.la.to_multiple_higher(aggfunc="sum", as_of_date=date_for_councils)
    gdp = pd.concat([gdp, higher_gdp])
    assert gdp["gdp"].isna().any() == False
    return gdp


def winsor(series: pd.Series, p: float = 0.05):
    array = winsorize(series, limits=(p, p))
    return pd.Series(array, index=series.index).sort_index()


def density_transform(series: pd.Series):
    """
    Density is scaled down after it is normalized
    So it presents as a pressure pushing apart dissimilar areas, but is far far less significant than the emissions.
    """
    return series * 0.25


def generate_emissions_similarity_df():
    """
    generate emissions similarity
    """

    df = get_la_emissions_data_with_population()
    df = df.loc[df["Year"] == 2020].drop(columns=["Year"])
    allowed_cols = (
        list(df.columns[:2])
        + [x for x in df.columns if "Total" in x and "Waste" not in x]
        + ["pop-2020", "area", "lower-or-unitary"]
    )
    df = df[allowed_cols]
    df = df.rename(columns=lambda x: x.split(":")[0]).drop(columns=["Total Emissions"])

    gdp = get_gdp_df()

    df = df.merge(gdp, on="local-authority-code")

    # we winsorize the pop-2020 data, but only for columns where lower-or-unitary is true
    # condition, value if true, default is value if false
    df["wpop"] = np.select(
        [df["lower-or-unitary"]], [winsor(df["pop-2020"])], default=df["pop-2020"]
    )
    df["public_sector_by_wpop"] = df["Public Sector Total"] / df["wpop"]
    df["transport_by_wpop"] = df["Transport Total"] / df["wpop"]
    df["pop_density"] = winsor(df["pop-2020"] / df["area"], p=0.05)
    df["domestic_by_pop"] = df["Domestic Total"] / df["pop-2020"]
    df["industry_by_gdp"] = df["Industry Total"] / df["gdp"]
    df["commerical_by_gdp"] = df["Commercial Total"] / df["gdp"]
    df["agriculture_by_gdp"] = df["Agriculture Total"] / df["gdp"]

    old_total_cols = [x for x in df.columns if "Total" in x]
    df = df.drop(columns=old_total_cols)

    d = df.copy().set_index("local-authority-code")

    d = d.drop(
        columns=["pop-2020", "area", "lower-or-unitary", "official-name", "gdp", "wpop"]
    )

    d.to_csv(
        Path("data", "interim", "la_emissions_similarity.csv"),
        index=True,
    )


def merge_results():
    df = pd.read_csv(Path("data", "interim", "la_emissions_similarity.csv"))
    labels = pd.read_csv(Path("data", "interim", "cluster_labels.csv"))
    df = df.merge(labels, on="local-authority-code")
    df.to_csv(
        Path("data", "packages", "uk_local_authority_emissions_data", "la_labels.csv"),
        index=False,
    )


def generate_comparisons():
    generate_emissions_similarity_df()
    run_notebook(Path("notebooks", "cluster_emissions.ipynb"))
    merge_results()


if __name__ == "__main__":
    generate_comparisons()
