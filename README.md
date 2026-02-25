# Otomata Tools

Boîte à outils Python open-source pour l'automatisation business par agents IA. Chaque outil est utilisable en **CLI** (scripts standalone) ou en **librairie** (import dans vos agents/workers).

Fait partie de l'écosystème [otomata.tech](https://otomata.tech) — les outils sont la couche d'exécution que les agents utilisent pour agir sur le monde réel.

## Outils disponibles

| Catégorie | Outils | Auth |
|-----------|--------|------|
| **Google Workspace** | Drive, Docs, Sheets, Slides | Service Account |
| **Gmail** | Lire, rechercher, envoyer | OAuth2 user |
| **Notion** | Pages, databases, search | API key |
| **Entreprises FR** | Sirene (INSEE), Recherche Entreprises, stock local | API key |
| **Prospection** | Kaspr, Hunter, Apollo, ClearBit, Lemlist | API keys |
| **Browser** | LinkedIn, Crunchbase, Pappers, Indeed, G2 | Session cookies |
| **Communication** | Slack, Resend (email) | API keys |
| **IA** | Anthropic (admin/batch), Groq, Mistral, Gemini | API keys |
| **Compta** | Pennylane | API key |
| **Search** | Serper, SerpAPI | API key |
| **Media** | Unsplash, Figma | API keys |

## Principe : zéro secret dans le repo

Les outils ne stockent aucun secret. Les credentials sont fournies par :
- **L'appelant** (mode librairie) : injection explicite au constructeur
- **L'environnement** (mode CLI) : variables d'env ou `~/.otomata/secrets.env`

```python
# Mode librairie — l'appelant (worker, agent) gère ses secrets
from otomata.tools.sirene import SireneClient
client = SireneClient(api_key="xxx")

from otomata.tools.google.gmail.lib.gmail_client import GmailClient
client = GmailClient(credentials=oauth_creds)
```

```bash
# Mode CLI — secrets résolus depuis l'environnement
mkdir -p ~/.otomata
cat > ~/.otomata/secrets.env << 'EOF'
SIRENE_API_KEY=xxx
GOOGLE_SERVICE_ACCOUNT='{"type":"service_account",...}'
GOOGLE_OAUTH_CLIENT='{"installed":{"client_id":"...","client_secret":"..."}}'
NOTION_API_KEY=secret_xxx
EOF
```

## Installation

```bash
pip install git+https://github.com/AlexisLaporte/otomata-tools.git

# Avec extras
pip install "otomata[browser] @ git+https://github.com/AlexisLaporte/otomata-tools.git"
pip install "otomata[all] @ git+https://github.com/AlexisLaporte/otomata-tools.git"
```

Extras : `browser` (Patchright), `stock` (pyarrow/pandas), `company-fr`, `ai` (Anthropic), `all`.

## Utilisation

### CLI

```bash
otomata google drive-list --folder-id xxx
otomata google drive-download <file-id> output.pdf
otomata sirene search --naf 62.01Z --limit 10
otomata kaspr enrich --linkedin-slug "john-doe-123"
otomata notion search "query"
otomata hunter domain example.com
```

### Librairie

```python
from otomata.tools.google.drive.lib.drive_client import DriveClient
files = DriveClient().list_files(folder_id="xxx")

from otomata.tools.sirene import SireneClient
results = SireneClient(api_key="xxx").search(naf=["62.01Z"], limit=50)

from otomata.tools.google.gmail.lib.gmail_client import GmailClient
client = GmailClient()
client.send(to="a@b.com", subject="Test", body="Hello")
```

## Setup Google

- **Drive, Docs, Sheets, Slides** (Service Account) : [docs/google-service-account-setup.md](docs/google-service-account-setup.md)
- **Gmail** (OAuth2 user) : [docs/gmail-oauth-setup.md](docs/gmail-oauth-setup.md)

## Développement

```bash
git clone https://github.com/AlexisLaporte/otomata-tools.git
cd otomata-tools
pip install -e ".[dev,all]"
otomata config  # Vérifier les secrets détectés
```

## Versioning

Version dans `otomata/__init__.py`. Auto-update check au premier import (désactiver : `OTOMATA_NO_UPDATE_CHECK=1`).

```bash
git tag v0.X.0 && git push origin v0.X.0
gh release create v0.X.0 --title "v0.X.0" --notes "..."
```
