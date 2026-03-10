---
name: oto-google
description: Gmail, Google Drive, Google Docs. Use for reading/sending emails, searching inbox, listing Drive files, reading Docs.
---

# Google Workspace (oto google)

Prérequis : `oto` installé (pipx), OAuth tokens dans `~/.otomata/google-oauth-token-*.json`.

## Comptes Google

Toujours passer `-a <compte>`. Pas de défaut.

| Compte | Email |
|--------|-------|
| `otomata` | alexis@otomata.tech |
| `perso` | alexis.laporte@gmail.com |
| `sarahetalexis` | sarah.et.alexis.sl@gmail.com |

## Gmail

```bash
# Rechercher des emails
oto google gmail-search "from:user@example.com is:unread" -n 20 -a otomata

# Lister les emails récents
oto google gmail-list --query "is:unread" -n 10 -a perso

# Lire un email (par message ID, obtenu via search/list)
oto google gmail-get MESSAGE_ID -a otomata

# Télécharger les pièces jointes
oto google gmail-attachments MESSAGE_ID -o ./downloads -a otomata

# Créer un brouillon
oto google gmail-draft --to "dest@example.com" --subject "Sujet" --body "Contenu" -a otomata

# Envoyer un email
oto google gmail-send --to "dest@example.com" --subject "Sujet" --body "Contenu" --cc "cc@example.com" -f file.pdf -a otomata

# Archiver des messages
oto google gmail-archive MESSAGE_ID1 MESSAGE_ID2 -a otomata
oto google gmail-archive --query "from:newsletter@spam.com" -a otomata
```

## Drive

```bash
# Lister les fichiers
oto google drive-list --limit 50
oto google drive-list --folder-id FOLDER_ID
oto google drive-list --query "name contains 'facture'"

# Télécharger un fichier
oto google drive-download FILE_ID output.pdf
```

## Docs

```bash
# Lister les titres d'un document
oto google docs-headings DOC_ID

# Lire une section par titre
oto google docs-section DOC_ID "Titre de la section"
```

## Auth

```bash
# Lister les comptes configurés
oto google auth --list

# Configurer un nouveau compte (ouvre le navigateur)
oto google auth nom_du_compte
```

## Exemples

1. **Trouver les emails non lus d'un expéditeur** :
   `oto google gmail-search "from:comptable@cabinet.fr is:unread" -a otomata`

2. **Envoyer un email avec pièce jointe** :
   `oto google gmail-send --to "client@example.com" --subject "Facture" --body "Ci-joint la facture." -f facture.pdf -a otomata`

3. **Lire un Google Doc** :
   `oto google docs-headings 1abc...xyz` puis `oto google docs-section 1abc...xyz "Introduction"`
