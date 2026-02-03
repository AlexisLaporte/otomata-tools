# TODO / Roadmap

## Browser automation

### Multi-backend support
Currently using Patchright (undetectable Playwright). Consider adding alternative backends:

- **Vercel Agent-Browser** (https://github.com/vercel-labs/agent-browser)
  - CLI Rust/Node, fast
  - `snapshot` command returns accessibility tree (AI-friendly)
  - Stateful across commands
  - `--profile` for session persistence
  - Installation: `npm install -g agent-browser`

  Could be useful for AI agent workflows where we want structured DOM info rather than raw HTML/text.

- **Chrome DevTools MCP** (https://github.com/anthropics/chrome-devtools-mcp)
  - 26 outils : navigation, input, debugging, network, performance, emulation
  - Accès direct aux DevTools (console, network, DOM)
  - Tests E2E déclaratifs en YAML
  - Installation: `claude mcp add chrome-devtools npx chrome-devtools-mcp@latest`

  Complémentaire à Patchright : utile pour debugging dev web, pas pour scraping (nécessite Chrome UI).

### Ideas
- [ ] Abstract backend selection in BrowserClient (patchright vs agent-browser)
- [ ] Add `snapshot()` method that returns structured accessibility tree (format AI-friendly)
- [ ] Évaluer Chrome DevTools MCP pour tests E2E (complémentaire à Patchright)

## Scrapers

- [x] Indeed jobs scraper
- [x] LinkedIn profile scraper
- [x] Crunchbase, Pappers, G2 scrapers
- [ ] Generic "login + navigate + extract" pattern

## Google tools

- [ ] Calendar integration
- [ ] Gmail (or use MCP server?)

## Notion tools

- [ ] Batch page creation
- [ ] Database sync with external sources
