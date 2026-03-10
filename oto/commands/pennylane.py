"""Pennylane accounting commands."""

import typer
from typing import Optional

app = typer.Typer(help="Pennylane accounting API")


@app.command("company")
def company():
    """Get company info from Pennylane."""
    import json
    from oto.tools.pennylane import PennylaneClient

    client = PennylaneClient()
    result = client.get_company_info()
    print(json.dumps(result, indent=2, ensure_ascii=False))


@app.command("fiscal-years")
def fiscal_years():
    """Get fiscal years."""
    import json
    from oto.tools.pennylane import PennylaneClient

    client = PennylaneClient()
    result = client.get_fiscal_years()
    print(json.dumps(result, indent=2, ensure_ascii=False))


@app.command("trial-balance")
def trial_balance(
    start: str = typer.Option(..., "--start", help="Period start (YYYY-MM-DD)"),
    end: str = typer.Option(..., "--end", help="Period end (YYYY-MM-DD)"),
):
    """Get trial balance for a period."""
    import json
    from oto.tools.pennylane import PennylaneClient

    client = PennylaneClient()
    result = client.get_trial_balance(start, end)
    print(json.dumps(result, indent=2, ensure_ascii=False))


@app.command("ledger-accounts")
def ledger_accounts():
    """Get all ledger accounts."""
    import json
    from oto.tools.pennylane import PennylaneClient

    client = PennylaneClient()
    result = client.get_ledger_accounts()
    print(json.dumps(result, indent=2, ensure_ascii=False))


@app.command("customer-invoices")
def customer_invoices(
    max_pages: int = typer.Option(50, "--max-pages", help="Max pages to fetch"),
):
    """Get customer invoices."""
    import json
    from oto.tools.pennylane import PennylaneClient

    client = PennylaneClient()
    result = client.get_customer_invoices(max_pages=max_pages)
    print(json.dumps(result, indent=2, ensure_ascii=False))


@app.command("supplier-invoices")
def supplier_invoices(
    max_pages: int = typer.Option(50, "--max-pages", help="Max pages to fetch"),
):
    """Get supplier invoices."""
    import json
    from oto.tools.pennylane import PennylaneClient

    client = PennylaneClient()
    result = client.get_supplier_invoices(max_pages=max_pages)
    print(json.dumps(result, indent=2, ensure_ascii=False))


@app.command("categories")
def categories():
    """Get expense categories."""
    import json
    from oto.tools.pennylane import PennylaneClient

    client = PennylaneClient()
    result = client.get_categories()
    print(json.dumps(result, indent=2, ensure_ascii=False))


@app.command("complete")
def complete(
    year: int = typer.Option(2025, "--year", help="Fiscal year to fetch"),
):
    """Fetch complete financial data for a year."""
    import json
    from oto.tools.pennylane import PennylaneClient

    client = PennylaneClient()
    result = client.fetch_complete_data(year=year)
    print(json.dumps(result, indent=2, ensure_ascii=False))
