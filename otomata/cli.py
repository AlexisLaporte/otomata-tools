"""Otomata CLI - unified entry point for all tools."""

import typer
from typing import Optional

app = typer.Typer(
    name="otomata",
    help="CLI tools for automating tasks with Google, Notion, and more.",
    no_args_is_help=True,
)


# Google subcommands
google_app = typer.Typer(help="Google Workspace tools (Drive, Docs, Sheets, Slides)")
app.add_typer(google_app, name="google")


@google_app.command("drive-list")
def google_drive_list(
    folder_id: Optional[str] = typer.Option(None, help="Filter by parent folder ID"),
    query: Optional[str] = typer.Option(None, help="Custom query filter"),
    limit: int = typer.Option(100, help="Max results"),
):
    """List files in Google Drive."""
    from otomata.tools.google.drive.lib.drive_client import DriveClient
    from otomata.tools.google.credentials import get_credentials
    import json

    creds = get_credentials()
    client = DriveClient()
    files = client.list_files(folder_id=folder_id, query=query, page_size=limit)
    print(json.dumps({"count": len(files), "files": files}, indent=2))


@google_app.command("drive-download")
def google_drive_download(
    file_id: str = typer.Argument(..., help="Google Drive file ID"),
    output: str = typer.Argument(..., help="Output path"),
):
    """Download a file from Google Drive."""
    from otomata.tools.google.drive.lib.drive_client import DriveClient

    client = DriveClient()
    result = client.download_file(file_id, output)
    print(f"Downloaded: {result['filename']} -> {result['output_path']}")


@google_app.command("docs-headings")
def google_docs_headings(
    doc_id: str = typer.Argument(..., help="Google Docs document ID"),
):
    """List headings in a Google Doc."""
    from otomata.tools.google.docs.lib.docs_client import DocsClient
    import json

    client = DocsClient()
    headings = client.list_headings(doc_id)
    print(json.dumps(headings, indent=2))


@google_app.command("docs-section")
def google_docs_section(
    doc_id: str = typer.Argument(..., help="Google Docs document ID"),
    heading: str = typer.Argument(..., help="Heading text to find"),
):
    """Get content of a section in a Google Doc."""
    from otomata.tools.google.docs.lib.docs_client import DocsClient

    client = DocsClient()
    section = client.get_section_content(doc_id, heading)
    if section:
        print(f"# {section.title}\n")
        print(section.content)
    else:
        print(f"Section not found: {heading}")
        raise typer.Exit(1)


# Notion subcommands
notion_app = typer.Typer(help="Notion tools")
app.add_typer(notion_app, name="notion")


@notion_app.command("search")
def notion_search(
    query: str = typer.Argument(..., help="Search query"),
    filter_type: Optional[str] = typer.Option(None, help="Filter by type (page, database)"),
):
    """Search Notion workspace."""
    from otomata.tools.notion.lib.notion_client import NotionClient
    import json

    client = NotionClient()
    results = client.search(query, filter_type=filter_type)
    print(json.dumps(results, indent=2, ensure_ascii=False))


@notion_app.command("page")
def notion_page(
    page_id: str = typer.Argument(..., help="Notion page ID"),
    blocks: bool = typer.Option(False, "--blocks", "-b", help="Include page blocks/content"),
):
    """Get a Notion page."""
    from otomata.tools.notion.lib.notion_client import NotionClient
    import json

    client = NotionClient()
    page = client.get_page(page_id)

    if blocks:
        page["blocks"] = client.get_page_blocks(page_id, recursive=True)

    print(json.dumps(page, indent=2, ensure_ascii=False))


@notion_app.command("database")
def notion_database(
    database_id: str = typer.Argument(..., help="Notion database ID"),
    query: bool = typer.Option(False, "--query", "-q", help="Query database entries"),
    limit: int = typer.Option(100, help="Max results when querying"),
):
    """Get a Notion database schema or query its entries."""
    from otomata.tools.notion.lib.notion_client import NotionClient
    import json

    client = NotionClient()

    if query:
        results = client.query_database(database_id, page_size=limit)
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        db = client.get_database(database_id)
        print(json.dumps(db, indent=2, ensure_ascii=False))


# Browser subcommands
browser_app = typer.Typer(help="Browser automation tools (LinkedIn, Crunchbase, Indeed, etc.)")
app.add_typer(browser_app, name="browser")


@browser_app.command("linkedin-company")
def linkedin_company(
    url: str = typer.Argument(..., help="LinkedIn company URL"),
    cookie: Optional[str] = typer.Option(None, envvar="LINKEDIN_COOKIE", help="li_at cookie"),
    identity: str = typer.Option("default", help="Identity for rate limiting"),
    profile: Optional[str] = typer.Option(None, help="Chrome profile directory path"),
    channel: Optional[str] = typer.Option(None, envvar="BROWSER_CHANNEL", help="Chrome channel (chrome, chrome-beta, chromium)"),
    no_rate_limit: bool = typer.Option(False, "--no-rate-limit", help="Disable rate limiting"),
    headless: bool = typer.Option(True, help="Run headless"),
):
    """Scrape LinkedIn company page."""
    import asyncio
    import json
    from otomata.tools.browser import LinkedInClient

    async def run():
        async with LinkedInClient(cookie=cookie, identity=identity, profile=profile, channel=channel, headless=headless, rate_limit=not no_rate_limit) as client:
            return await client.scrape_company(url)

    result = asyncio.run(run())
    print(json.dumps(result, indent=2, ensure_ascii=False))


@browser_app.command("linkedin-profile")
def linkedin_profile(
    url: str = typer.Argument(..., help="LinkedIn profile URL"),
    cookie: Optional[str] = typer.Option(None, envvar="LINKEDIN_COOKIE", help="li_at cookie"),
    identity: str = typer.Option("default", help="Identity for rate limiting"),
    profile: Optional[str] = typer.Option(None, help="Chrome profile directory path"),
    channel: Optional[str] = typer.Option(None, envvar="BROWSER_CHANNEL", help="Chrome channel (chrome, chrome-beta, chromium)"),
    no_rate_limit: bool = typer.Option(False, "--no-rate-limit", help="Disable rate limiting"),
    headless: bool = typer.Option(True, help="Run headless"),
):
    """Scrape LinkedIn profile page."""
    import asyncio
    import json
    from otomata.tools.browser import LinkedInClient

    async def run():
        async with LinkedInClient(cookie=cookie, identity=identity, profile=profile, channel=channel, headless=headless, rate_limit=not no_rate_limit) as client:
            return await client.scrape_profile(url)

    result = asyncio.run(run())
    print(json.dumps(result, indent=2, ensure_ascii=False))


@browser_app.command("linkedin-search")
def linkedin_search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(5, help="Max results"),
    cookie: Optional[str] = typer.Option(None, envvar="LINKEDIN_COOKIE", help="li_at cookie"),
    profile: Optional[str] = typer.Option(None, help="Chrome profile directory path"),
    channel: Optional[str] = typer.Option(None, envvar="BROWSER_CHANNEL", help="Chrome channel (chrome, chrome-beta, chromium)"),
    no_rate_limit: bool = typer.Option(False, "--no-rate-limit", help="Disable rate limiting"),
    headless: bool = typer.Option(True, help="Run headless"),
):
    """Search LinkedIn companies."""
    import asyncio
    import json
    from otomata.tools.browser import LinkedInClient

    async def run():
        async with LinkedInClient(cookie=cookie, profile=profile, channel=channel, headless=headless, rate_limit=not no_rate_limit) as client:
            return await client.search_companies(query, limit=limit)

    result = asyncio.run(run())
    print(json.dumps(result, indent=2, ensure_ascii=False))


@browser_app.command("linkedin-people")
def linkedin_people(
    slug: str = typer.Argument(..., help="LinkedIn company slug"),
    limit: int = typer.Option(20, help="Max results"),
    cookie: Optional[str] = typer.Option(None, envvar="LINKEDIN_COOKIE", help="li_at cookie"),
    profile: Optional[str] = typer.Option(None, help="Chrome profile directory path"),
    channel: Optional[str] = typer.Option(None, envvar="BROWSER_CHANNEL", help="Chrome channel (chrome, chrome-beta, chromium)"),
    no_rate_limit: bool = typer.Option(False, "--no-rate-limit", help="Disable rate limiting"),
    headless: bool = typer.Option(True, help="Run headless"),
):
    """List people from a LinkedIn company page."""
    import asyncio
    import json
    from otomata.tools.browser import LinkedInClient

    async def run():
        async with LinkedInClient(cookie=cookie, profile=profile, channel=channel, headless=headless, rate_limit=not no_rate_limit) as client:
            return await client.get_company_people(slug, limit=limit)

    result = asyncio.run(run())
    print(json.dumps(result, indent=2, ensure_ascii=False))


@browser_app.command("linkedin-employees")
def linkedin_employees(
    company: str = typer.Argument(..., help="LinkedIn company slug"),
    keywords: Optional[str] = typer.Option(None, help="Title keywords (comma-separated)"),
    limit: int = typer.Option(10, help="Max results"),
    cookie: Optional[str] = typer.Option(None, envvar="LINKEDIN_COOKIE", help="li_at cookie"),
    profile: Optional[str] = typer.Option(None, help="Chrome profile directory path"),
    channel: Optional[str] = typer.Option(None, envvar="BROWSER_CHANNEL", help="Chrome channel (chrome, chrome-beta, chromium)"),
    no_rate_limit: bool = typer.Option(False, "--no-rate-limit", help="Disable rate limiting"),
    headless: bool = typer.Option(True, help="Run headless"),
):
    """Search company employees on LinkedIn."""
    import asyncio
    import json
    from otomata.tools.browser import LinkedInClient

    async def run():
        kw_list = keywords.split(",") if keywords else None
        async with LinkedInClient(cookie=cookie, profile=profile, channel=channel, headless=headless, rate_limit=not no_rate_limit) as client:
            return await client.search_employees(company, keywords=kw_list, limit=limit)

    result = asyncio.run(run())
    print(json.dumps(result, indent=2, ensure_ascii=False))


@browser_app.command("crunchbase-company")
def crunchbase_company(
    slug: str = typer.Argument(..., help="Company slug or URL"),
    headless: bool = typer.Option(True, help="Run headless"),
):
    """Get company from Crunchbase."""
    import asyncio
    import json
    from otomata.tools.browser import CrunchbaseClient

    async def run():
        async with CrunchbaseClient(headless=headless) as client:
            return await client.get_company(slug)

    result = asyncio.run(run())
    print(json.dumps(result, indent=2, ensure_ascii=False))


@browser_app.command("pappers-siren")
def pappers_siren(
    siren: str = typer.Argument(..., help="SIREN number"),
    headless: bool = typer.Option(True, help="Run headless"),
):
    """Get French company data from Pappers."""
    import asyncio
    import json
    from otomata.tools.browser import PappersClient

    async def run():
        async with PappersClient(headless=headless) as client:
            return await client.get_company_by_siren(siren)

    result = asyncio.run(run())
    print(json.dumps(result, indent=2, ensure_ascii=False))


@browser_app.command("indeed-search")
def indeed_search(
    query: str = typer.Argument(..., help="Job search query"),
    location: str = typer.Option("", help="Location"),
    country: str = typer.Option("fr", help="Country code (fr, us, uk, de)"),
    limit: int = typer.Option(25, help="Max results"),
    headless: bool = typer.Option(True, help="Run headless"),
):
    """Search jobs on Indeed."""
    import asyncio
    import json
    from otomata.tools.browser import IndeedClient

    async def run():
        async with IndeedClient(country=country, headless=headless) as client:
            return await client.search_jobs(query, location=location, max_results=limit)

    result = asyncio.run(run())
    print(json.dumps(result, indent=2, ensure_ascii=False))


@browser_app.command("g2-reviews")
def g2_reviews(
    url: str = typer.Argument(..., help="G2 product reviews URL"),
    limit: int = typer.Option(50, help="Max reviews"),
    headless: bool = typer.Option(True, help="Run headless"),
):
    """Scrape product reviews from G2."""
    import asyncio
    import json
    from otomata.tools.browser import G2Client

    async def run():
        async with G2Client(headless=headless) as client:
            return await client.get_product_reviews(url, max_reviews=limit)

    result = asyncio.run(run())
    print(json.dumps(result, indent=2, ensure_ascii=False))


# Sirene subcommands (French company data)
sirene_app = typer.Typer(help="French company data (INSEE SIRENE, API Entreprises)")
app.add_typer(sirene_app, name="sirene")


@sirene_app.command("search")
def sirene_search(
    query: Optional[str] = typer.Argument(None, help="Company name to search"),
    naf: Optional[str] = typer.Option(None, "--naf", help="NAF codes (comma-separated, e.g. 62.01Z,62.02A)"),
    employees: Optional[str] = typer.Option(None, "--employees", help="Employee ranges (e.g. 11,12)"),
    dept: Optional[str] = typer.Option(None, "--dept", help="Department code for SIRET search"),
    postal: Optional[str] = typer.Option(None, "--postal", help="Postal code for SIRET search"),
    city: Optional[str] = typer.Option(None, "--city", help="City name for SIRET search"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max results"),
):
    """Search French companies in INSEE SIRENE database."""
    import json
    from otomata.tools.sirene import SireneClient

    client = SireneClient()
    naf_list = naf.split(",") if naf else None
    emp_list = employees.split(",") if employees else None

    # Use SIRET search when name or location filters are specified
    if query or dept or postal or city:
        results = client.search_siret(
            name=query,
            naf=naf_list,
            employees=emp_list,
            postal_code=postal,
            city=city,
            headquarters_only=True,
            limit=limit,
        )
        companies = results.get("etablissements", [])
        print(json.dumps({
            "total": results.get("header", {}).get("total", len(companies)),
            "count": len(companies),
            "etablissements": companies,
        }, indent=2, ensure_ascii=False))
    else:
        results = client.search(
            naf=naf_list,
            employees=emp_list,
            limit=limit,
        )
        companies = results.get("unitesLegales", [])
        print(json.dumps({
            "total": results.get("header", {}).get("total", len(companies)),
            "count": len(companies),
            "unitesLegales": companies,
        }, indent=2, ensure_ascii=False))


@sirene_app.command("get")
def sirene_get(
    siren: str = typer.Argument(..., help="SIREN number (9 digits)"),
):
    """Get company details by SIREN."""
    import json
    from otomata.tools.sirene import SireneClient

    client = SireneClient()
    company = client.get_by_siren(siren)
    print(json.dumps(company, indent=2, ensure_ascii=False))


@sirene_app.command("siret")
def sirene_siret(
    siret: str = typer.Argument(..., help="SIRET number (14 digits)"),
):
    """Get establishment details by SIRET."""
    import json
    from otomata.tools.sirene import SireneClient

    client = SireneClient()
    establishment = client.get_siret(siret)
    print(json.dumps(establishment, indent=2, ensure_ascii=False))


@sirene_app.command("headquarters")
def sirene_headquarters(
    siren: str = typer.Argument(..., help="SIREN number (9 digits)"),
):
    """Get company headquarters with address."""
    import json
    from otomata.tools.sirene import SireneClient

    client = SireneClient()
    hq = client.get_headquarters(siren)
    if hq:
        print(json.dumps(hq, indent=2, ensure_ascii=False))
    else:
        print("Headquarters not found")
        raise typer.Exit(1)


@sirene_app.command("suggest-naf")
def sirene_suggest_naf(
    description: str = typer.Argument(..., help="Activity description in French"),
    limit: int = typer.Option(3, "--limit", "-n", help="Max suggestions"),
):
    """Suggest NAF codes from activity description using AI."""
    import json
    from otomata.tools.naf import NAFSuggester

    suggester = NAFSuggester()
    suggestions = suggester.suggest(description, limit=limit)

    result = [{
        "code": s.code,
        "label": s.label,
        "confidence": s.confidence,
        "reason": s.reason,
    } for s in suggestions]

    print(json.dumps({"suggestions": result}, indent=2, ensure_ascii=False))


@sirene_app.command("entreprises")
def sirene_entreprises(
    query: Optional[str] = typer.Argument(None, help="Search query"),
    naf: Optional[str] = typer.Option(None, "--naf", help="NAF codes (comma-separated)"),
    dept: Optional[str] = typer.Option(None, "--dept", help="Department code"),
    ca_min: Optional[int] = typer.Option(None, "--ca-min", help="Min turnover (€)"),
    ca_max: Optional[int] = typer.Option(None, "--ca-max", help="Max turnover (€)"),
    limit: int = typer.Option(25, "--limit", "-n", help="Max results"),
):
    """Search companies with enriched data (directors, finances) via API Entreprises."""
    import json
    from otomata.tools.sirene import EntreprisesClient

    client = EntreprisesClient()
    naf_list = naf.split(",") if naf else None

    results = client.search(
        query=query,
        naf=naf_list,
        departement=dept,
        ca_min=ca_min,
        ca_max=ca_max,
        per_page=limit,
    )
    print(json.dumps(results, indent=2, ensure_ascii=False))


# Stock subcommands
stock_app = typer.Typer(help="SIRENE stock file for batch operations (~2GB local file)")
sirene_app.add_typer(stock_app, name="stock")


@stock_app.command("status")
def stock_status():
    """Show stock file status."""
    from otomata.tools.sirene import SireneStock

    stock = SireneStock()
    print(f"Path: {stock.stock_file}")
    print(f"Available: {'Yes' if stock.is_available else 'No'}")

    if stock.is_available:
        print(f"Size: {stock.file_size_gb:.2f} GB")
        age = stock.file_age_days
        if age:
            print(f"Age: {age:.0f} days")

    if stock.is_downloading:
        print("Status: Downloading...")


@stock_app.command("download")
def stock_download(
    force: bool = typer.Option(False, "--force", "-f", help="Re-download even if exists"),
):
    """Download SIRENE stock file (~2GB from data.gouv.fr)."""
    from otomata.tools.sirene import SireneStock

    stock = SireneStock()

    if stock.is_available and not force:
        print(f"Stock file already exists: {stock.stock_file}")
        print(f"Size: {stock.file_size_gb:.2f} GB, Age: {stock.file_age_days:.0f} days")
        print("Use --force to re-download")
        return

    stock.download(force=force)


@stock_app.command("addresses")
def stock_addresses(
    sirens: str = typer.Argument(..., help="SIREN numbers (comma-separated)"),
):
    """Get headquarters addresses from stock file (batch mode)."""
    import json
    from otomata.tools.sirene import SireneStock

    stock = SireneStock()
    siren_list = [s.strip() for s in sirens.split(",")]
    addresses = stock.get_headquarters_addresses(siren_list)
    print(json.dumps(addresses, indent=2, ensure_ascii=False))


# Search subcommands (Serper)
search_app = typer.Typer(help="Web and news search (Serper)")
app.add_typer(search_app, name="search")


@search_app.command("web")
def search_web(
    query: str = typer.Option(..., "--query", "-q", help="Search query"),
    num: int = typer.Option(10, "--num", "-n", help="Number of results"),
    tbs: Optional[str] = typer.Option(None, help="Time filter (e.g. qdr:y)"),
):
    """Search the web via Serper (Google)."""
    import json
    from otomata.tools.serper import SerperClient

    client = SerperClient()
    result = client.search(query, num=num, tbs=tbs)
    print(json.dumps(result, indent=2, ensure_ascii=False))


@search_app.command("news")
def search_news(
    query: str = typer.Option(..., "--query", "-q", help="Search query"),
    num: int = typer.Option(10, "--num", "-n", help="Number of results"),
    tbs: Optional[str] = typer.Option(None, help="Time filter (e.g. qdr:y)"),
):
    """Search news via Serper (Google News)."""
    import json
    from otomata.tools.serper import SerperClient

    client = SerperClient()
    result = client.search_news(query, num=num, tbs=tbs)
    print(json.dumps(result, indent=2, ensure_ascii=False))


# Kaspr subcommands
kaspr_app = typer.Typer(help="Kaspr contact enrichment")
app.add_typer(kaspr_app, name="kaspr")


@kaspr_app.command("enrich")
def kaspr_enrich(
    linkedin_slug: str = typer.Argument(..., help="LinkedIn profile slug"),
    name: Optional[str] = typer.Option(None, "--name", help="Person full name"),
):
    """Enrich a LinkedIn profile with Kaspr (email, phone)."""
    import json
    from otomata.tools.kaspr import KasprClient

    client = KasprClient()
    result = client.enrich_linkedin(linkedin_slug, name=name)
    print(json.dumps(result, indent=2, ensure_ascii=False))


# Hunter subcommands
hunter_app = typer.Typer(help="Hunter.io email tools")
app.add_typer(hunter_app, name="hunter")


@hunter_app.command("domain")
def hunter_domain(
    domain: str = typer.Argument(..., help="Domain to search"),
    limit: int = typer.Option(10, "--limit", "-n", help="Max results"),
):
    """Search emails for a domain via Hunter."""
    import json
    from otomata.tools.hunter import HunterClient

    client = HunterClient()
    result = client.domain_search(domain, limit=limit)
    print(json.dumps(result, indent=2, ensure_ascii=False))


@hunter_app.command("find")
def hunter_find(
    domain: str = typer.Argument(..., help="Domain"),
    name: str = typer.Option(..., "--name", help="Full name"),
):
    """Find email for a person at a domain via Hunter."""
    import json
    from otomata.tools.hunter import HunterClient

    client = HunterClient()
    result = client.email_finder(domain, full_name=name)
    print(json.dumps(result, indent=2, ensure_ascii=False))


@hunter_app.command("verify")
def hunter_verify(
    email: str = typer.Argument(..., help="Email to verify"),
):
    """Verify an email address via Hunter."""
    import json
    from otomata.tools.hunter import HunterClient

    client = HunterClient()
    result = client.email_verifier(email)
    print(json.dumps(result, indent=2, ensure_ascii=False))


# Lemlist subcommands
lemlist_app = typer.Typer(help="Lemlist campaign & lead management")
app.add_typer(lemlist_app, name="lemlist")


@lemlist_app.command("campaigns")
def lemlist_campaigns():
    """List all Lemlist campaigns."""
    import json
    from otomata.tools.lemlist import LemlistClient

    client = LemlistClient()
    campaigns = client.list_campaigns()
    result = [{"id": c.id, "name": c.name, "status": c.status, "senders": c.senders} for c in campaigns]
    print(json.dumps(result, indent=2, ensure_ascii=False))


@lemlist_app.command("leads")
def lemlist_leads(
    campaign_id: str = typer.Argument(..., help="Campaign ID"),
):
    """List leads in a campaign."""
    import json
    from otomata.tools.lemlist import LemlistClient

    client = LemlistClient()
    leads = client.get_all_leads(campaign_id)
    print(json.dumps(leads, indent=2, ensure_ascii=False))


@lemlist_app.command("add-lead")
def lemlist_add_lead(
    campaign_id: str = typer.Argument(..., help="Campaign ID"),
    email: str = typer.Option(..., "--email", "-e", help="Lead email"),
    first_name: str = typer.Option(None, "--first-name", help="First name"),
    last_name: str = typer.Option(None, "--last-name", help="Last name"),
    company: str = typer.Option(None, "--company", help="Company name"),
    phone: str = typer.Option(None, "--phone", help="Phone number"),
    linkedin: str = typer.Option(None, "--linkedin", help="LinkedIn URL"),
):
    """Add a lead to a Lemlist campaign."""
    import json
    from otomata.tools.lemlist import LemlistClient
    from otomata.tools.lemlist.client import Lead

    client = LemlistClient()
    lead = Lead(
        email=email,
        firstName=first_name,
        lastName=last_name,
        companyName=company,
        phone=phone,
        linkedinUrl=linkedin,
    )
    result = client.add_lead(campaign_id, lead)
    print(json.dumps(result, indent=2, ensure_ascii=False))


@lemlist_app.command("delete-lead")
def lemlist_delete_lead(
    campaign_id: str = typer.Argument(..., help="Campaign ID"),
    email: str = typer.Argument(..., help="Lead email to remove"),
):
    """Remove a lead from a Lemlist campaign."""
    import json
    from otomata.tools.lemlist import LemlistClient

    client = LemlistClient()
    result = client.delete_lead(campaign_id, email)
    print(json.dumps(result, indent=2, ensure_ascii=False))


@lemlist_app.command("export")
def lemlist_export(
    campaign_id: str = typer.Argument(..., help="Campaign ID"),
):
    """Export leads from a campaign as CSV."""
    from otomata.tools.lemlist import LemlistClient

    client = LemlistClient()
    csv_data = client.export_leads(campaign_id)
    print(csv_data)


# Top-level company command
@app.command("company")
def company_info(
    siren: str = typer.Argument(..., help="SIREN number (9 digits)"),
):
    """Get French company info by SIREN (directors, finances, address). No API key needed."""
    import json
    from otomata.tools.sirene import EntreprisesClient

    client = EntreprisesClient()
    result = client.get_by_siren(siren)

    if not result:
        print(f"Company not found: {siren}")
        raise typer.Exit(1)

    print(json.dumps(result, indent=2, ensure_ascii=False))


# Help command
@app.command("help")
def show_help():
    """Show all available commands with usage examples."""
    print("""otomata CLI — all commands

COMPANY INFO
  otomata company <SIREN>                          Get company by SIREN (directors, finances, address)

BROWSER AUTOMATION
  otomata browser linkedin-company <URL>            Scrape LinkedIn company page
  otomata browser linkedin-profile <URL>            Scrape LinkedIn profile
  otomata browser linkedin-search <QUERY>           Search LinkedIn companies
  otomata browser linkedin-people <SLUG>            List people from LinkedIn company
  otomata browser linkedin-employees <SLUG>         Search employees by keywords
    LinkedIn options: --cookie, --profile <dir>, --channel (chrome|chrome-beta|chromium)
  otomata browser pappers-siren <SIREN>             Scrape Pappers company page
  otomata browser crunchbase-company <SLUG>         Scrape Crunchbase company
  otomata browser indeed-search <QUERY>             Search jobs on Indeed
  otomata browser g2-reviews <URL>                  Scrape G2 product reviews

SEARCH (Serper/Google)
  otomata search web -q <QUERY> [--num 5]           Web search
  otomata search news -q <QUERY> [--tbs qdr:y]      News search

CONTACT ENRICHMENT
  otomata kaspr enrich <SLUG> [--name "..."]        Get email/phone via Kaspr
  otomata hunter domain <DOMAIN> [--limit 10]       Find emails for a domain
  otomata hunter find <DOMAIN> --name "..."          Find email for a person
  otomata hunter verify <EMAIL>                     Verify an email

FRENCH COMPANY DATA (SIRENE)
  otomata sirene search [QUERY] [--naf ...] [--dept ...]  Search INSEE SIRENE
  otomata sirene get <SIREN>                        Get by SIREN (needs API key)
  otomata sirene entreprises [QUERY]                Search API Entreprises
  otomata sirene headquarters <SIREN>               Get HQ address
  otomata sirene suggest-naf "description"          Suggest NAF codes (AI)

GOOGLE WORKSPACE
  otomata google drive-list [--folder-id ...]       List Drive files
  otomata google drive-download <FILE_ID> <PATH>    Download from Drive
  otomata google docs-headings <DOC_ID>             List headings in a Doc
  otomata google docs-section <DOC_ID> <HEADING>    Get section content

NOTION
  otomata notion search <QUERY>                     Search Notion
  otomata notion page <PAGE_ID> [--blocks]          Get a page
  otomata notion database <DB_ID> [--query]         Get/query a database

PENNYLANE (Accounting)
  otomata pennylane company                          Get company info
  otomata pennylane fiscal-years                     Get fiscal years
  otomata pennylane trial-balance --start ... --end   Get trial balance
  otomata pennylane ledger-accounts                  Get ledger accounts
  otomata pennylane customer-invoices                Get customer invoices
  otomata pennylane supplier-invoices                Get supplier invoices
  otomata pennylane categories                       Get expense categories
  otomata pennylane complete [--year 2025]            Fetch all data for a year

CONFIG
  otomata config                                    Show secrets status

All commands output JSON on stdout. Use --help on any command for details.""")


# Pennylane subcommands
pennylane_app = typer.Typer(help="Pennylane accounting API")
app.add_typer(pennylane_app, name="pennylane")


@pennylane_app.command("company")
def pennylane_company():
    """Get company info from Pennylane."""
    import json
    from otomata.tools.pennylane import PennylaneClient

    client = PennylaneClient()
    result = client.get_company_info()
    print(json.dumps(result, indent=2, ensure_ascii=False))


@pennylane_app.command("fiscal-years")
def pennylane_fiscal_years():
    """Get fiscal years."""
    import json
    from otomata.tools.pennylane import PennylaneClient

    client = PennylaneClient()
    result = client.get_fiscal_years()
    print(json.dumps(result, indent=2, ensure_ascii=False))


@pennylane_app.command("trial-balance")
def pennylane_trial_balance(
    start: str = typer.Option(..., "--start", help="Period start (YYYY-MM-DD)"),
    end: str = typer.Option(..., "--end", help="Period end (YYYY-MM-DD)"),
):
    """Get trial balance for a period."""
    import json
    from otomata.tools.pennylane import PennylaneClient

    client = PennylaneClient()
    result = client.get_trial_balance(start, end)
    print(json.dumps(result, indent=2, ensure_ascii=False))


@pennylane_app.command("ledger-accounts")
def pennylane_ledger_accounts():
    """Get all ledger accounts."""
    import json
    from otomata.tools.pennylane import PennylaneClient

    client = PennylaneClient()
    result = client.get_ledger_accounts()
    print(json.dumps(result, indent=2, ensure_ascii=False))


@pennylane_app.command("customer-invoices")
def pennylane_customer_invoices(
    max_pages: int = typer.Option(50, "--max-pages", help="Max pages to fetch"),
):
    """Get customer invoices."""
    import json
    from otomata.tools.pennylane import PennylaneClient

    client = PennylaneClient()
    result = client.get_customer_invoices(max_pages=max_pages)
    print(json.dumps(result, indent=2, ensure_ascii=False))


@pennylane_app.command("supplier-invoices")
def pennylane_supplier_invoices(
    max_pages: int = typer.Option(50, "--max-pages", help="Max pages to fetch"),
):
    """Get supplier invoices."""
    import json
    from otomata.tools.pennylane import PennylaneClient

    client = PennylaneClient()
    result = client.get_supplier_invoices(max_pages=max_pages)
    print(json.dumps(result, indent=2, ensure_ascii=False))


@pennylane_app.command("categories")
def pennylane_categories():
    """Get expense categories."""
    import json
    from otomata.tools.pennylane import PennylaneClient

    client = PennylaneClient()
    result = client.get_categories()
    print(json.dumps(result, indent=2, ensure_ascii=False))


@pennylane_app.command("complete")
def pennylane_complete(
    year: int = typer.Option(2025, "--year", help="Fiscal year to fetch"),
):
    """Fetch complete financial data for a year."""
    import json
    from otomata.tools.pennylane import PennylaneClient

    client = PennylaneClient()
    result = client.fetch_complete_data(year=year)
    print(json.dumps(result, indent=2, ensure_ascii=False))


# Anthropic Admin API subcommands
anthropic_app = typer.Typer(help="Anthropic Admin API (usage & cost tracking)")
app.add_typer(anthropic_app, name="anthropic")


@anthropic_app.command("usage")
def anthropic_usage(
    days: int = typer.Option(7, "--days", "-d", help="Number of days to look back"),
    bucket: str = typer.Option("1d", "--bucket", "-b", help="Bucket width: 1m, 1h, 1d"),
    group_by: Optional[str] = typer.Option("model", "--group-by", "-g", help="Group by: model, api_key_id, workspace_id, service_tier"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Filter to specific model"),
):
    """Get token usage report."""
    import json
    from otomata.tools.anthropic import AnthropicAdminClient

    client = AnthropicAdminClient()
    groups = [g.strip() for g in group_by.split(",")] if group_by else None
    models = [model] if model else None
    data = client.get_usage(bucket_width=bucket, group_by=groups, models=models,
                            limit=days if bucket == "1d" else None)
    print(json.dumps(data, indent=2, ensure_ascii=False))


@anthropic_app.command("cost")
def anthropic_cost(
    days: int = typer.Option(30, "--days", "-d", help="Number of days to look back"),
    group_by: Optional[str] = typer.Option(None, "--group-by", "-g", help="Group by: workspace_id, description"),
):
    """Get cost report (daily, USD)."""
    import json
    from otomata.tools.anthropic import AnthropicAdminClient

    client = AnthropicAdminClient()
    groups = [g.strip() for g in group_by.split(",")] if group_by else None
    data = client.get_costs(group_by=groups)
    print(json.dumps(data, indent=2, ensure_ascii=False))


@anthropic_app.command("summary")
def anthropic_summary(
    days: int = typer.Option(7, "--days", "-d", help="Number of days to look back"),
):
    """Daily usage summary with estimated costs by model."""
    import json
    from otomata.tools.anthropic import AnthropicAdminClient

    client = AnthropicAdminClient()
    result = client.get_daily_summary(days=days)
    print(json.dumps(result, indent=2, ensure_ascii=False))


@anthropic_app.command("today")
def anthropic_today():
    """Today's usage and estimated cost."""
    import json
    from otomata.tools.anthropic import AnthropicAdminClient

    client = AnthropicAdminClient()
    result = client.get_today_cost()
    print(json.dumps(result, indent=2, ensure_ascii=False))


# Config commands
@app.command("config")
def show_config():
    """Show current configuration and detected secrets."""
    from pathlib import Path
    from otomata.config import _find_project_secrets, _get_user_secrets, get_secret

    project_secrets = _find_project_secrets()
    user_secrets = _get_user_secrets()

    print("Secrets files:")
    print(f"  Project: {project_secrets or '.otomata/secrets.env (not found)'}")
    print(f"  User:    {user_secrets}{' (exists)' if user_secrets.exists() else ' (not found)'}")
    print()
    print("Secrets status:")
    secrets = [
        "GOOGLE_SERVICE_ACCOUNT",
        "NOTION_API_KEY",
        "LINKEDIN_COOKIE",
        "SIRENE_API_KEY",
        "GROQ_API_KEY",
        "ANTHROPIC_ADMIN_API_KEY",
    ]
    for name in secrets:
        status = "✓" if get_secret(name) else "✗"
        print(f"  {status} {name}")


if __name__ == "__main__":
    app()
