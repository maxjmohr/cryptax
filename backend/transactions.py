import os

import polars as pl
from dotenv import load_dotenv

# Load the environment variables (locally)
dotenv_path: str = os.path.join(os.path.dirname(__file__), "./../.env")
try:
    load_dotenv(dotenv_path)
except Exception:
    print(f"No .env file found at {dotenv_path}, skipping...")
    pass


class Transactions:
    # Class elements we expect
    __slots__: tuple = (
        "RAW_TRANSACTIONS_PATH",
        "df",
    )

    def load_environment_variables(self, var) -> None:
        """Load environment variables into class attributes.
        Args:
            var (str): The name of the environment variable to load.
        """
        value: str | None = os.environ.get(var)

        if value is None:
            raise EnvironmentError(f"Environment variable {var} is not set.")

        setattr(self, var, value)

    def __init__(self) -> None:
        """Initialize the class"""
        # Load the environment variables
        env_vars: list[str] = [
            "RAW_TRANSACTIONS_PATH",
        ]

        for var in env_vars:
            self.load_environment_variables(var)

        # Load transaction data
        self.load_transaction_data()

        # Group transaction fiat and coin records
        self.group_transaction_fiat_coin_records()

        # Calculate coin prices
        self.calculate_coin_prices()

        # Allocate EUR transactions to fiat
        self.allocate_eur_transactions_to_fiat()

        # Reorder columns and sort
        self.df = self.df.select(
            [
                "User_ID",
                "UTC_Time",
                "Account",
                "Operation",
                "Coin",
                "Change_Coin",
                "Currency",
                "Change_Fiscal",
                "Price_per_Coin",
                "source_file",
            ]
        ).sort("UTC_Time", descending=True)

    def find_all_transaction_files(self) -> list[str]:
        """Find all transaction files in the RAW_TRANSACTIONS_PATH directory.
        Returns:
            list[str]: A list of file paths.
        """
        transaction_files: list[str] = []

        for root, _, files in os.walk(self.RAW_TRANSACTIONS_PATH):
            for file in files:
                if file.endswith(".csv"):
                    transaction_files.append(os.path.join(root, file))

        if not transaction_files:
            raise FileNotFoundError(
                f"No transaction files found in {self.RAW_TRANSACTIONS_PATH}"
            )
        return transaction_files

    def load_transaction_data(self) -> None:
        """Load all transaction data from CSV files into a single DataFrame.
        Returns:
            self.df: A DataFrame containing all transaction data.
        """
        # Get all transaction file paths
        transaction_files: list[str] = self.find_all_transaction_files()
        dataframes: list[pl.DataFrame] = []

        # Read files
        for file in transaction_files:
            # Read raw file
            df: pl.DataFrame = pl.read_csv(file)

            # If there are no transactions, skip
            if df.height == 0:
                continue

            # Convert UTC_Time to datetime
            df = df.with_columns(pl.col("UTC_Time").str.to_datetime().alias("UTC_Time"))

            # Add a source column and store
            df = df.with_columns(
                pl.lit(file).str.split("/").list.last().alias("source_file")
            )
            dataframes.append(df)

        if not dataframes:
            raise ValueError("No dataframes to concatenate.")

        # Concatenate all dataframes
        self.df = pl.concat(dataframes, how="vertical")

    def group_transaction_fiat_coin_records(self) -> None:
        """For every transaction, we have 2 entries: 1 for the fiat currency and 1 for the coin and their gains. These records are always 1-2 seconds apart.
        The goal is to group these records together as 1 entry.
        """
        # Get the df and a copy to merge into the main df later
        # The main df will filter out Operation="Transaction Related" or "Binance Convert" and Coin="EUR"
        main_df = self.df.filter(
            ~(
                (pl.col("Operation").is_in(["Transaction Related", "Binance Convert"]))
                & (pl.col("Coin") == "EUR")
            )
        ).rename({"Change": "Change_Coin"})

        # The fiscal df will only contain Operation="Transaction Related" and Coin="EUR"
        fiscal_df = (
            self.df.filter(
                (pl.col("Operation").is_in(["Transaction Related", "Binance Convert"]))
                & (pl.col("Coin") == "EUR")
            )
            .select(
                [
                    "User_ID",
                    "UTC_Time",
                    "Account",
                    "Operation",
                    pl.col("Coin").alias("Currency"),
                    pl.col("Change").alias("Change_Fiscal"),
                ]
            )
            .sort("UTC_Time")  # Important for join_asof
        )

        # Join both dataframes on User_ID, Account, Operation and UTC_Time within 2 seconds
        joined_df: pl.DataFrame = main_df.sort("UTC_Time").join_asof(
            fiscal_df,
            on="UTC_Time",
            # by=["User_ID", "Account", "Operation"],
            strategy="nearest",
            tolerance="2s",
        )

        # Assert that the length of Operation="Transaction Related" is same as filled Change_Fiscal
        assert (
            self.df.filter(
                (pl.col("Operation").is_in(["Transaction Related", "Binance Convert"]))
                & (pl.col("Coin") == "EUR")
            ).height
            == joined_df.filter(pl.col("Change_Fiscal").is_not_null()).height
        ), "Not all fiscal records were matched to their coin records."

        self.df = joined_df

    def calculate_coin_prices(self) -> None:
        """Calculate coin prices based on Change_Coin and Change_Fiscal."""
        self.df = self.df.with_columns(
            abs((pl.col("Change_Fiscal") / pl.col("Change_Coin"))).alias(
                "Price_per_Coin"
            )
        )

    def allocate_eur_transactions_to_fiat(self) -> None:
        """Allocate some columns to the fiat columns
        Coin -> Currency
        Change_Coin -> Change_Fiat
        """
        self.df = self.df.with_columns(
            # Coin -> Currency
            pl.when(pl.col("Coin") == "EUR")
            .then("Coin")
            .otherwise(pl.col("Currency"))
            .alias("Currency"),
            # Change_Coin -> Change_Fiscal
            pl.when(pl.col("Coin") == "EUR")
            .then(pl.col("Change_Coin"))
            .otherwise(pl.col("Change_Fiscal"))
            .alias("Change_Fiscal"),
            # Empty Coin
            pl.when(pl.col("Coin") == "EUR")
            .then(None)
            .otherwise(pl.col("Coin"))
            .alias("Coin"),
            # Empty Change_Coin
            pl.when(pl.col("Coin") == "EUR")
            .then(None)
            .otherwise(pl.col("Change_Coin"))
            .alias("Change_Coin"),
        )

    def output_excel(self, file_path: str) -> None:
        """Output the DataFrame to an Excel file.
        Args:
            file_path (str): The path to the output Excel file.
        """
        self.df.write_excel(file_path)


if __name__ == "__main__":
    transaction_data = Transactions()
    print(transaction_data.df)
    # Export as xlsx
    transaction_data.output_excel("output_transactions.xlsx")
