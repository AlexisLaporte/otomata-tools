---
name: oto-google
description: Gmail, Google Drive, Google Docs. Use for reading/sending emails, searching inbox, listing Drive files, reading Docs.
---

# Google Workspace (oto google)

Prérequis : `oto` installé (pipx), OAuth tokens dans `~/.otomata/google-oauth-token-*.json`.

## Google accounts

Always pass `-a <account>`. No default. List configured accounts with `oto google auth --list`.

Add a new account: `oto google auth <name>` (opens browser for OAuth flow).

## Gmail

```bash
# Rechercher des emails
oto google gmail search "from:user@example.com is:unread" -n 20 -a myaccount

# Lister les emails récents
oto google gmail list --query "is:unread" -n 10 -a myaccount

# Lire un email (par message ID, obtenu via search/list)
oto google gmail get MESSAGE_ID -a myaccount

# Télécharger les pièces jointes
oto google gmail attachments MESSAGE_ID -o ./downloads -a myaccount

# Créer un brouillon
oto google gmail draft --to "dest@example.com" --subject "Sujet" --body "Contenu" -a myaccount

# Envoyer un email
oto google gmail send --to "dest@example.com" --subject "Sujet" --body "Contenu" --cc "cc@example.com" -f file.pdf -a myaccount

# Archiver des messages
oto google gmail archive MESSAGE_ID1 MESSAGE_ID2 -a myaccount
oto google gmail archive --query "from:newsletter@spam.com" -a myaccount
```

## Drive

```bash
# Lister les fichiers
oto google drive list --limit 50 -a myaccount
oto google drive list --folder-id FOLDER_ID -a myaccount
oto google drive list --query "name contains 'facture'" -a myaccount

# Télécharger un fichier
oto google drive download FILE_ID output.pdf -a myaccount

# Uploader un fichier
oto google drive upload file.pdf --folder-id FOLDER_ID -a myaccount
```

## Docs

```bash
# Lister les titres d'un document
oto google docs headings DOC_ID -a myaccount

# Lire une section par titre
oto google docs section DOC_ID "Titre de la section" -a myaccount
```

## Sheets

```bash
# Lire un spreadsheet
oto google sheets read SPREADSHEET_ID -a myaccount
oto google sheets read SPREADSHEET_ID "Sheet1!A1:D10" --format json -a myaccount
```

## Calendar

```bash
# Événements du jour
oto google calendar today -a myaccount

# Événements à venir
oto google calendar upcoming --days 7 -a myaccount

# Rechercher
oto google calendar search "réunion" --past 30 -a myaccount
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
   `oto google gmail search "from:comptable@cabinet.fr is:unread" -a myaccount`

2. **Envoyer un email avec pièce jointe** :
   `oto google gmail send --to "client@example.com" --subject "Facture" --body "Ci-joint la facture." -f facture.pdf -a myaccount`

3. **Lire un Google Doc** :
   `oto google docs headings 1abc...xyz -a myaccount` puis `oto google docs section 1abc...xyz "Introduction" -a myaccount`
