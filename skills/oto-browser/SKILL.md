---
name: oto-browser
description: Browser automation for LinkedIn, Crunchbase, Pappers, Indeed, G2. Use for scraping profiles, company pages, job searches, reviews.
---

# Browser Automation (oto browser / oto linkedin)

Prérequis : `oto` installé (pipx), `LINKEDIN_COOKIE` (li_at) pour LinkedIn.

Toutes les commandes browser tournent en headless par défaut. Ajouter `--no-headless` pour debug visuel.

## LinkedIn (oto linkedin)

```bash
# Profil d'une personne
oto linkedin profile "https://www.linkedin.com/in/john-doe/"

# Page entreprise
oto linkedin company "https://www.linkedin.com/company/otomata/"

# Recherche d'entreprises
oto linkedin search "fintech" --limit 10

# Liste des employés d'une entreprise (par slug)
oto linkedin people otomata --limit 20

# Recherche d'employés avec filtres
oto linkedin employees otomata --keywords "CTO,CEO" --limit 10

# Recherche de personnes par mots-clés + géo
oto linkedin search-people "credit manager" --geo 105015875 --limit 50 --pages 5

# Posts d'un profil
oto linkedin posts "https://www.linkedin.com/in/john-doe/" -n 10
```

Options communes LinkedIn : `--cookie`, `--cdp-url`, `--profile`, `--channel`, `--no-rate-limit`, `--no-headless`.

## Crunchbase

```bash
# Fiche entreprise
oto browser crunchbase-company "otomata"
```

## Pappers (entreprises FR)

```bash
# Données entreprise par SIREN
oto browser pappers-siren "123456789"
```

## Indeed (offres d'emploi)

```bash
# Recherche d'offres
oto browser indeed-search "développeur python" --location "Paris" --country fr --limit 25
```

## G2 (avis produit)

```bash
# Scraper les avis
oto browser g2-reviews "https://www.g2.com/products/xxx/reviews" --limit 50
```

## Exemples

1. **Profil LinkedIn** : `oto linkedin profile "https://www.linkedin.com/in/alexis-laporte/"`
2. **Trouver les C-levels d'une boîte** : `oto linkedin employees stripe --keywords "CEO,CTO,CFO" --limit 5`
3. **Offres Indeed à Lyon** : `oto browser indeed-search "data engineer" --location "Lyon" --limit 20`
