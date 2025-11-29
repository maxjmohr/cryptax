from taxreport import TaxReport


def main() -> None:
    """Build pdf tax report with all relevant sections"""
    # Build tax report
    report = TaxReport()
    report.output_pdf()


if __name__ == "__main__":
    main()
