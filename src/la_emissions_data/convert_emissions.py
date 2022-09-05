"""
Convert the 2020 emissions file

"""
import pandas as pd
import data_common.pandas.df_extensions.la
from pathlib import Path


def columns_to_names_and_units() -> dict[str, tuple[str, str]]:
    return {
        # these headers are sadly specific to a year so may need updated
        # when new data comes out
        "Industry Electricity": ("Industry Electricity", "kt CO2"),
        "Industry Gas ": ("Industry Gas", "kt CO2"),
        "Large Industrial Installations": ("Large Industrial Installations", "kt CO2"),
        "Industry 'Other'": ("Industrial Other Fuels", "kt CO2"),
        "Agriculture Electricity": ("Agriculture Electricity", "kt CO2"),
        "Agriculture Gas": ("Agriculture", "kt CO2"),
        "Agriculture 'Other'": ("Agriculture 'Other'", "kt CO2"),
        "Agriculture Total": ("Agriculture Total", "kt CO2"),
        "Industry Total": ("Industry Total", "kt CO2"),
        "Commercial Electricity": ("Commercial Electricity", "kt CO2"),
        "Commercial Gas ": ("Commercial Gas", "kt CO2"),
        "Commercial 'Other'": ("Commercial Other Fuels", "kt CO2"),
        "Commercial Total": ("Commercial Total", "kt CO2"),
        "Public Sector Electricity": ("Public Sector Electricity", "kt CO2"),
        "Public Sector Gas ": ("Public Sector Gas", "kt CO2"),
        "Public Sector 'Other'": ("Public Sector Other Fuels", "kt CO2"),
        "Public Sector Total": ("Public Sector Total", "kt CO2"),
        "Domestic Electricity": ("Domestic Electricity", "kt CO2"),
        "Domestic Gas": ("Domestic Gas", "kt CO2"),
        "Domestic 'Other'": ("Domestic Other Fuels", "kt CO2"),
        "Domestic Total": ("Domestic Total", "kt CO2"),
        "Road Transport (A roads)": ("Road Transport (A roads)", "kt CO2"),
        "Road Transport (Minor roads)": ("Road Transport (Minor roads)", "kt CO2"),
        "Transport 'Other'": ("Transport Other", "kt CO2"),
        "Transport Total": ("Transport Total", "kt CO2"),
        "Waste Management 'Other'": ("Waste Management Other", "kt CO2"),
        "Waste Management Total": ("Waste Management Total", "kt CO2"),
        "Grand Total": ("Total Emissions", "kt CO2"),
        "Population ('000s, mid-year estimate)": (
            "Population",
            "000s",
        ),
        "Per Capita Emissions (tCO2)": ("Per Person Emissions", "t"),
        "Area (km2)": ("Area", "km2"),
        "Emissions per km2 (kt CO2)": ("Emissions per km2", "kt"),
    }


def update_to_modern(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return the input dataframe with modern councils calculcated from the input
    """

    # convert to modern lower tier/unitary councils
    df = df.la.to_current().la.just_lower_tier()

    # get higher geographies from lower geographies
    county_df = df.la.to_higher(aggfunc="sum")
    combined_df = df.la.to_higher(aggfunc="sum", comparison_column="combined-authority")

    # need to recreate because cannot be calculated from sum

    for hdf in [df, county_df, combined_df]:
        # both total emissions and population are stored in 1000s, so this keeps to tons
        hdf["Per Person Emissions:t"] = (
            hdf["Total Emissions:kt CO2"] / hdf["Population:000s"]
        )
        hdf["Emissions per km2:kt"] = hdf["Total Emissions:kt CO2"] / hdf["Area:km2"]

    return pd.concat([df, county_df, combined_df]).drop(columns=["Year"])


def convert_emissions():
    """
    Convert the 2020 emissions file to the more standardised version we use, and fill in
    newer and higher geogrpahies
    """
    file_path = Path(
        "data", "raw", "external", "UK-local-authority-ghg-emissions-2020.xlsx"
    )
    df = pd.read_excel(str(file_path), sheet_name="2_1", header=4)

    df = df.rename(
        columns={x: f"{y[0]}:{y[1]}" for x, y in columns_to_names_and_units().items()}
    )
    df = df.rename(columns={"Calendar Year": "Year"})

    df = df.loc[~df["Local Authority Code"].isna()]

    df = df.la.create_code_column(
        from_type="gss", source_col="Local Authority Code"
    ).drop(
        columns=[
            "Local Authority Code",
            "Local Authority",
            "Second Tier Authority",
            "Region/Country",
        ]
    )

    # get modern and higher level geographies
    df = (
        df.groupby("Year")
        .apply(update_to_modern)
        .reset_index()
        .drop(columns=["level_1"])
        .la.get_council_info(["official-name"])
    )

    other_columns = list(df.columns[2:-1])
    df = df[["Year", "local-authority-code", "official-name"] + other_columns]

    df.to_csv(
        Path(
            "data",
            "packages",
            "uk_local_authority_emissions_data",
            "local_authority_emissions.csv",
        ),
        index=False,
    )


if __name__ == "__main__":
    convert_emissions()
