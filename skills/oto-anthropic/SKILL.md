---
name: oto-anthropic
description: Anthropic API usage and cost tracking. Use for checking API costs, token usage, daily summaries.
---

# Usage & Coûts Anthropic (oto anthropic)

Prérequis : `oto` installé (pipx), `ANTHROPIC_ADMIN_API_KEY` dans l'environnement.

## Commandes

```bash
# Usage tokens (7 derniers jours, groupé par modèle)
oto anthropic usage

# Usage personnalisé
oto anthropic usage --days 30 --bucket 1d --group-by model
oto anthropic usage --days 7 --model claude-sonnet-4-20250514

# Coûts (30 derniers jours)
oto anthropic cost
oto anthropic cost --days 60 --group-by workspace_id

# Résumé quotidien avec coûts estimés par modèle
oto anthropic summary --days 7

# Coût d'aujourd'hui
oto anthropic today
```

Options `--bucket` : `1m` (minute), `1h` (heure), `1d` (jour).
Options `--group-by` : `model`, `api_key_id`, `workspace_id`, `service_tier`.

## Exemples

1. **Combien j'ai dépensé aujourd'hui** : `oto anthropic today`
2. **Usage par modèle cette semaine** : `oto anthropic summary --days 7`
3. **Coûts du mois** : `oto anthropic cost --days 30`
