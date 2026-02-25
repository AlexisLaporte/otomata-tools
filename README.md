# Otomata Tools

Python toolkit for business automation — company data, browser scraping, CRM, AI, Google Workspace, and more. Works as a CLI and as an importable library.

**Website:** [otomata.tech](https://otomata.tech)

## Installation

```bash
# CLI (standalone)
pipx install git+https://github.com/AlexisLaporte/otomata-tools.git

# As a dependency
pip install git+https://github.com/AlexisLaporte/otomata-tools.git

# Pin a version
pip install git+https://github.com/AlexisLaporte/otomata-tools.git@v0.2.0

# With extras
pip install "otomata[browser,ai] @ git+https://github.com/AlexisLaporte/otomata-tools.git"
```

### Extras

| Extra | What it adds |
|-------|-------------|
| `browser` | Patchright (undetectable Playwright) |
| `stock` | pyarrow + pandas for SIRENE bulk data |
| `company-fr` | French company API clients |
| `ai` | Anthropic + Mistral SDKs |
| `communication` | Resend email |
| `marketing` | Marketing tools |
| `crm` | CRM clients |
| `search` | Web search APIs |
| `media` | Media APIs |
| `pennylane` | Pennylane accounting |
| `all` | Everything above |

## Configuration

### CLI mode

Secrets are loaded from `.otomata/secrets.env` files:

1. **Project** — `.otomata/secrets.env` in current directory (walks up 4 levels)
2. **User** — `~/.otomata/secrets.env`

```bash
mkdir -p ~/.otomata
cat > ~/.otomata/secrets.env << 'EOF'
SIRENE_API_KEY=xxx
GROQ_API_KEY=xxx
GOOGLE_SERVICE_ACCOUNT='{"type":"service_account",...}'
NOTION_API_KEY=secret_xxx
EOF
```

### Library mode

Pass secrets explicitly — no magic:

```python
from otomata.tools.sirene import SireneClient
client = SireneClient(api_key="xxx")
```

Check which secrets are configured:

```bash
otomata config
```

## Tools

### French Company Data (SIRENE)

Search the INSEE SIRENE database (29M+ establishments), API Entreprises (directors, finances), and NAF code suggestion via AI.

```bash
# Search companies
otomata sirene search --naf 62.01Z --employees 11,12 --limit 10
otomata sirene search "unitag" --dept 31

# Get company details
otomata sirene get 443061841
otomata sirene headquarters 443061841

# Enriched search (directors, finances) — no API key needed
otomata sirene entreprises "unitag" --ca-min 100000

# AI-powered NAF code suggestion
otomata sirene suggest-naf "SaaS software development"

# Quick company lookup
otomata company 443061841

# Bulk addresses from stock file (~2GB local)
otomata sirene stock download
otomata sirene stock addresses 443061841,552032534
```

```python
from otomata.tools.sirene import SireneClient, EntreprisesClient, SireneStock

client = SireneClient(api_key="xxx")
results = client.search(naf=["62.01Z"], employees=["11", "12"], limit=50)
hq = client.get_headquarters("443061841")

entreprises = EntreprisesClient()
results = entreprises.search(query="unitag", ca_min=100000)
directors = entreprises.get_directors("443061841")
```

**Secrets:** `SIRENE_API_KEY` (INSEE), `GROQ_API_KEY` (NAF suggestion)

### Browser Automation

Scrape sites with no public API using Patchright (undetectable Chromium). Supports persistent sessions and rate limiting.

```bash
# LinkedIn
otomata browser linkedin-company https://linkedin.com/company/example
otomata browser linkedin-profile https://linkedin.com/in/johndoe
otomata browser linkedin-search "AI startups"
otomata browser linkedin-people example-company --limit 50
otomata browser linkedin-employees example-company --keywords "CTO,VP Engineering"

# Other sites
otomata browser crunchbase-company example-company
otomata browser pappers-siren 443061841
otomata browser indeed-search "python developer" --location Paris --limit 25
otomata browser g2-reviews https://www.g2.com/products/example/reviews --limit 100
```

```python
from otomata.tools.browser import LinkedInClient, CrunchbaseClient

async with LinkedInClient(cookie="li_at=...", headless=True) as client:
    company = await client.scrape_company("https://linkedin.com/company/example")
    employees = await client.search_employees("example", keywords=["CTO"])
```

**Secrets:** `LINKEDIN_COOKIE` (optional, for authenticated scraping)

### Google Workspace

Drive, Docs, Sheets, and Slides via service account.

```bash
otomata google drive-list --folder-id xxx
otomata google drive-download <file-id> output.pdf
otomata google docs-headings <doc-id>
otomata google docs-section <doc-id> "Introduction"
```

```python
from otomata.tools.google.drive.lib.drive_client import DriveClient
from otomata.tools.google.docs.lib.docs_client import DocsClient

drive = DriveClient()
files = drive.list_files(folder_id="xxx")

docs = DocsClient()
headings = docs.list_headings(doc_id)
section = docs.get_section_content(doc_id, "Introduction")
```

**Secret:** `GOOGLE_SERVICE_ACCOUNT` (JSON string)

### Notion

Search, read pages and databases.

```bash
otomata notion search "quarterly report"
otomata notion page <page-id> --blocks
otomata notion database <db-id> --query
```

```python
from otomata.tools.notion.lib.notion_client import NotionClient

notion = NotionClient()
results = notion.search("quarterly report")
page = notion.get_page(page_id)
entries = notion.query_database(db_id)
```

**Secret:** `NOTION_API_KEY`

### AI / LLM

Unified clients for Anthropic, Mistral, Groq, and Gemini (text + image generation).

```bash
otomata mistral chat "Summarize this contract" --model mistral-small-latest
otomata anthropic usage --days 7
otomata anthropic cost --days 30
otomata anthropic today
```

```python
from otomata.tools.mistral import MistralClient
from otomata.tools.groq import GroqClient
from otomata.tools.gemini import GeminiClient
from otomata.tools.anthropic import AnthropicAdminClient

# Text completion
mistral = MistralClient()
answer = mistral.complete("You are a lawyer.", "Analyze this clause...")

groq = GroqClient()
data = groq.complete_json("Extract entities.", text)

# Image generation (Gemini)
gemini = GeminiClient()
image_b64 = gemini.generate_image("Professional headshot, studio lighting")

# Anthropic usage & cost tracking
admin = AnthropicAdminClient()
today = admin.get_today_cost()
summary = admin.get_daily_summary(days=7)
```

**Secrets:** `MISTRAL_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `ANTHROPIC_ADMIN_API_KEY`

### Contact Enrichment

Find and verify professional emails and phone numbers.

```python
from otomata.tools.kaspr import KasprClient
from otomata.tools.hunter import HunterClient
from otomata.tools.zerobounce import ZeroBounceClient

# LinkedIn → email/phone
kaspr = KasprClient()
contact = kaspr.enrich_linkedin("john-doe-12345")

# Domain → emails
hunter = HunterClient()
emails = hunter.domain_search("example.com")
person = hunter.email_finder("example.com", full_name="John Doe")
hunter.email_verifier("john@example.com")

# Bulk email verification
zb = ZeroBounceClient()
results = zb.verify_batch(["a@example.com", "b@example.com"])
```

```bash
otomata kaspr enrich john-doe-12345 --name "John Doe"
otomata hunter domain example.com
otomata hunter find example.com --name "John Doe"
otomata hunter verify john@example.com
```

**Secrets:** `KASPR_API_KEY`, `HUNTER_API_KEY`, `ZEROBOUNCE_API_KEY`

### Sales & Outreach

Campaign management and B2B intelligence.

```python
from otomata.tools.lemlist import LemlistClient
from otomata.tools.apollo import ApolloClient

# Email campaigns
lemlist = LemlistClient()
campaigns = lemlist.list_campaigns()
lemlist.add_lead(campaign_id, Lead(email="john@example.com", firstName="John"))
stats = lemlist.get_campaign_stats(campaign_id)

# B2B lead search
apollo = ApolloClient()
companies = apollo.search_organizations(name="Stripe")
people = apollo.search_people(domain="stripe.com", titles=["CTO"])
jobs = apollo.get_job_postings("stripe.com")
```

```bash
otomata lemlist campaigns
otomata lemlist leads <campaign-id>
otomata lemlist add-lead <campaign-id> --email john@example.com --first-name John
```

**Secrets:** `LEMLIST_API_KEY`, `APOLLO_API_KEY`, `PHANTOMBUSTER_API_KEY`

### CRM

Clients for Attio and Folk CRM platforms.

```python
from otomata.tools.attio import AttioClient
from otomata.tools.folk import FolkClient

# Attio
attio = AttioClient()
companies = attio.companies.list()
attio.companies.create({"name": "Acme Corp"})

# Folk
folk = FolkClient()
people = folk.fetch_people()
folk.create_person({"name": "John Doe", "email": "john@example.com"})
```

**Secrets:** `ATTIO_API_KEY`, `FOLK_API_KEY`

### Web Search

Google search and news via Serper, job search via SerpAPI.

```bash
otomata search web -q "AI startup funding 2025" --num 5
otomata search news -q "Series A" --tbs qdr:m
```

```python
from otomata.tools.serper import SerperClient
from otomata.tools.serpapi import SerpAPIClient

serper = SerperClient()
results = serper.search("AI startup funding", num=10)
news = serper.search_news("Series A", tbs="qdr:m")
html = serper.scrape_page("https://example.com")

serpapi = SerpAPIClient()
jobs = serpapi.search_jobs("Google", "software engineer")
```

**Secrets:** `SERPER_API_KEY`, `SERPAPI_API_KEY`

### Accounting (Pennylane)

Fetch financial data from Pennylane.

```bash
otomata pennylane company
otomata pennylane trial-balance --start 2025-01-01 --end 2025-12-31
otomata pennylane customer-invoices
otomata pennylane complete --year 2025
```

```python
from otomata.tools.pennylane import PennylaneClient

pl = PennylaneClient()
balance = pl.get_trial_balance("2025-01-01", "2025-12-31")
invoices = pl.get_customer_invoices()
```

**Secret:** `PENNYLANE_API_KEY`

### Communication

Send emails and Slack messages.

```python
from otomata.tools.resend import ResendClient
from otomata.tools.slack import SlackClient

# Email
resend = ResendClient()
resend.send(to="john@example.com", subject="Hello", html="<p>Hi</p>")

# Slack
slack = SlackClient()
slack.post_message(channel="#general", text="Deploy complete")
slack.add_reaction(channel, timestamp, "white_check_mark")
```

**Secrets:** `RESEND_API_KEY`, `SLACK_BOT_TOKEN`

### Other Tools

| Tool | What it does | Secret |
|------|-------------|--------|
| **Figma** | Read files, export images, manage comments | `FIGMA_API_KEY` |
| **Unsplash** | Search stock photos | `UNSPLASH_API_KEY` |
| **Clearbit** | Company logo lookup (no auth) | — |
| **HitHorizons** | European company data | `HITHORIZONS_API_KEY` |
| **WTTJ** | Welcome to the Jungle job scraper (browser) | — |
| **Collective** | Collective.work freelance job scraper (browser) | — |

## Versioning

Version is defined in `otomata/__init__.py`. On import, otomata checks GitHub for newer releases in the background (3s timeout, non-blocking).

Disable the check:

```bash
OTOMATA_NO_UPDATE_CHECK=1 python my_script.py
```

### Publishing a new version

```bash
# 1. Bump __version__ in otomata/__init__.py
# 2. Commit + push
# 3. Tag + release
git tag v0.X.0
git push origin v0.X.0
gh release create v0.X.0 --title "v0.X.0" --notes "..."
```

## Development

```bash
git clone https://github.com/AlexisLaporte/otomata-tools.git
cd otomata-tools
pip install -e ".[dev,all]"
otomata config
```

## License

MIT
