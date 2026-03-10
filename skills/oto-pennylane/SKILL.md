---
name: oto-pennylane
description: Pennylane accounting API. Use for company finances, invoices, trial balance, ledger accounts, fiscal years.
---

# Comptabilité Pennylane (oto pennylane)

Prérequis : `oto` installé (pipx), `PENNYLANE_API_KEY` dans l'environnement.

## Commandes

```bash
# Info société
oto pennylane company

# Exercices fiscaux
oto pennylane fiscal-years

# Balance des comptes sur une période
oto pennylane trial-balance --start 2025-01-01 --end 2025-12-31

# Plan comptable (comptes)
oto pennylane ledger-accounts

# Factures clients
oto pennylane customer-invoices --max-pages 50

# Factures fournisseurs
oto pennylane supplier-invoices --max-pages 50

# Catégories de dépenses
oto pennylane categories

# Données financières complètes d'une année
oto pennylane complete --year 2025
```

## Exemples

1. **Situation financière** : `oto pennylane trial-balance --start 2025-01-01 --end 2025-06-30`
2. **Toutes les factures clients** : `oto pennylane customer-invoices`
3. **Export complet annuel** : `oto pennylane complete --year 2025`
