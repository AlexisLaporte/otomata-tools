---
name: oto-search
description: Web and news search via Serper (Google). Use for searching the web or news articles.
---

# Recherche Web & News (oto search)

Prérequis : `oto` installé (pipx), `SERPER_API_KEY` dans l'environnement.

## Commandes

```bash
# Recherche web
oto search web -q "query de recherche" -n 10

# Recherche actualités
oto search news -q "query de recherche" -n 10

# Avec filtre temporel (syntaxe Google tbs)
oto search web -q "startup fintech france" --tbs "qdr:m"   # dernier mois
oto search news -q "levée de fonds" --tbs "qdr:w"          # dernière semaine
```

Filtres temporels (`--tbs`) : `qdr:h` (heure), `qdr:d` (jour), `qdr:w` (semaine), `qdr:m` (mois), `qdr:y` (année).

## Exemples

1. **Recherche web** : `oto search web -q "otomata startup" -n 5`
2. **Actualités récentes** : `oto search news -q "intelligence artificielle france" -n 10 --tbs "qdr:w"`
