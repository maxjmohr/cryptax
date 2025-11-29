import os

import polars as pl
from dotenv import load_dotenv
from fpdf import FPDF

# Load the environment variables (locally)
dotenv_path: str = os.path.join(os.path.dirname(__file__), "./../../.env")
try:
    load_dotenv(dotenv_path)
except Exception:
    print(f"No .env file found at {dotenv_path}, skipping...")
    pass


class TaxReport:
    # Class elements we expect
    __slots__: tuple = ("FULL_NAME", "METHOD", "TAX_YEAR", "pdf")

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
            "FULL_NAME",
            "METHOD",
            "TAX_YEAR",
        ]

        for var in env_vars:
            self.load_environment_variables(var)

        # Setup pdf
        self.setup_pdf()

    def setup_pdf(self) -> None:
        """Setup the pdf with format and other configs"""
        pdf: FPDF = FPDF(orientation="portrait", format="A4")

        # Set font
        pdf.set_font("Helvetica")

        # TO BE CHANGED; ONLY FOR INITIAL DRAFT
        pdf.add_page(label_style="D", label_start=1)
        pdf.set_font("helvetica", size=12)
        pdf.cell(text="hello world")

        self.pdf = pdf

    def output_pdf(self, name: str = "tax_report", path: str = ".") -> None:
        """Function to output pdf to chosen directory path"""
        self.pdf.output(f"{path}/{name}.pdf")
