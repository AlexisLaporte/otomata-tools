---
name: oto-notion
description: Notion workspace. Use for searching pages, reading page content, querying databases.
---

# Notion (oto notion)

Prérequis : `oto` installé (pipx), `NOTION_API_KEY` dans l'environnement.

## Commandes

```bash
# Rechercher dans le workspace
oto notion search "query"
oto notion search "query" --filter-type page
oto notion search "query" --filter-type database

# Lire une page (propriétés)
oto notion page PAGE_ID

# Lire une page avec son contenu (blocs)
oto notion page PAGE_ID --blocks

# Voir le schéma d'une database
oto notion database DATABASE_ID

# Requêter les entrées d'une database
oto notion database DATABASE_ID --query --limit 50
```

## Exemples

1. **Trouver une page** : `oto notion search "roadmap produit"`
2. **Lire le contenu** : `oto notion page abc123 --blocks`
3. **Lister les entrées d'un CRM** : `oto notion database def456 --query --limit 100`
