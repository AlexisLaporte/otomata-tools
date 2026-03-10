---
name: oto-enrichment
description: Contact enrichment with Kaspr, Hunter, Lemlist. Use for finding emails/phones, verifying emails, managing outreach campaigns.
---

# Enrichissement contacts (oto enrichment)

Prérequis : `oto` installé (pipx).

## Kaspr (enrichissement LinkedIn → email/téléphone)

Secret : `KASPR_API_KEY`

```bash
# Enrichir un profil LinkedIn (slug = partie après /in/)
oto enrichment kaspr enrich "john-doe-123abc"
oto enrichment kaspr enrich "john-doe-123abc" --name "John Doe"
```

## Hunter (emails par domaine)

Secret : `HUNTER_API_KEY`

```bash
# Trouver les emails d'un domaine
oto enrichment hunter domain "example.com" -n 10

# Trouver l'email d'une personne
oto enrichment hunter find "example.com" --name "John Doe"

# Vérifier un email
oto enrichment hunter verify "john@example.com"
```

## Lemlist (campagnes outreach)

Secret : `LEMLIST_API_KEY`

```bash
# Lister les campagnes
oto enrichment lemlist campaigns

# Lister les leads d'une campagne
oto enrichment lemlist leads CAMPAIGN_ID

# Ajouter un lead
oto enrichment lemlist add-lead CAMPAIGN_ID -e "john@example.com" --first-name "John" --last-name "Doe" --company "Acme" --linkedin "https://linkedin.com/in/john-doe"

# Supprimer un lead
oto enrichment lemlist delete-lead CAMPAIGN_ID "john@example.com"

# Exporter les leads en CSV
oto enrichment lemlist export CAMPAIGN_ID
```

## Exemples

1. **Enrichir un contact** : `oto enrichment kaspr enrich "alexis-laporte-abc123" --name "Alexis Laporte"`
2. **Trouver les emails d'une boîte** : `oto enrichment hunter domain "otomata.tech" -n 20`
3. **Ajouter un lead à une campagne** : `oto enrichment lemlist add-lead cam_abc123 -e "prospect@company.com" --first-name "Marie" --company "TechCorp"`
