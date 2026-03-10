---
name: oto-sirene
description: SIRENE INSEE, données entreprises françaises. Use for searching companies by name/NAF/location, getting company details by SIREN/SIRET.
---

# SIRENE & Entreprises (oto sirene / oto company)

Prérequis : `oto` installé (pipx). `SIRENE_API_KEY` optionnel (API INSEE publique avec rate limit).

## Recherche d'entreprises (oto sirene)

```bash
# Recherche par nom
oto sirene search "otomata" -n 20

# Recherche par code NAF
oto sirene search --naf "6201Z,6202A" -n 50

# Recherche par département/ville
oto sirene search --dept "75" --city "Paris" -n 30

# Recherche par tranche d'effectif
oto sirene search --employees "11,12" -n 20

# Combiné
oto sirene search "conseil" --naf "7022Z" --dept "69" -n 10
```

## Détail entreprise

```bash
# Par SIREN (9 chiffres)
oto sirene get 123456789

# Par SIRET (14 chiffres)
oto sirene siret 12345678900001

# Siège social avec adresse
oto sirene headquarters 123456789
```

## Recherche enrichie (oto sirene entreprises)

Données enrichies : dirigeants, finances, via API Entreprises (pas de clé nécessaire).

```bash
oto sirene entreprises "fintech" --naf "6201Z" --dept "75" --ca-min 100000 --ca-max 10000000 -n 25
```

## Suggestion de codes NAF

```bash
oto sirene suggest-naf "développement de logiciels SaaS" -n 3
```

## Company info (oto company)

```bash
# Info entreprise par SIREN (dirigeants, finances, adresse) — pas de clé API
oto company info 123456789
```

## Stock SIRENE (batch, fichier local ~2GB)

```bash
oto sirene stock status
oto sirene stock download
oto sirene stock addresses "123456789,987654321"
```

## Exemples

1. **Chercher une entreprise** : `oto sirene search "alan" -n 5`
2. **Détails avec dirigeants** : `oto company info 880878145`
3. **ESN à Lyon** : `oto sirene search --naf "6201Z" --dept "69" -n 20`
