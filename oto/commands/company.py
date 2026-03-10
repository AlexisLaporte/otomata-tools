"""Company lookup command (SIREN multi-source)."""

import typer

app = typer.Typer(help="Company lookup")


@app.command("info")
def info(
    siren: str = typer.Argument(..., help="SIREN number (9 digits)"),
):
    """Get French company info by SIREN (directors, finances, address). No API key needed."""
    import json
    from oto.tools.sirene import EntreprisesClient

    client = EntreprisesClient()
    result = client.get_by_siren(siren)

    if not result:
        print(f"Company not found: {siren}")
        raise typer.Exit(1)

    print(json.dumps(result, indent=2, ensure_ascii=False))
