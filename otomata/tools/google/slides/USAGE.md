# Guide d'Utilisation - Google Slides Generator

## Configuration par Défaut

Le tool est **pré-configuré** pour 321:

- **Dossier par défaut:** `1lDh4H0cJKECdTv2y_zRbgifqjbDOvqbx`
- **Thème par défaut:** Template 321 (`1rA2YmYTA5P2O7GHgv9p3JwouO0lVVZEpZyKFFUKiVH4`)
- **Partage:** Ajoutez `--share` pour rendre public

## Utilisation Simple

### Générer une présentation

```bash
python3 tools/google-slides/generate_slides.py \
  --input mon-fichier.slides.yaml \
  --share
```

**Résultat:**
- ✅ Créée dans le dossier Drive partagé
- ✅ Thème 321 appliqué automatiquement
- ✅ Publique (anyone with link can view)
- ✅ URL retournée pour ouverture

### Formats de sortie

```bash
# URL simple
python3 tools/google-slides/generate_slides.py --input file.slides.yaml

# JSON détaillé
python3 tools/google-slides/generate_slides.py \
  --input file.slides.yaml \
  --output json
```

## Layouts YAML Supportés

### 1. Default (Title and body)
```yaml
- title: Mon Titre
  layout: default
  content: |
    Contenu principal
    - Points
    - Liste
```

### 2. Hero (Title only)
```yaml
- title: Grand Titre
  layout: hero
```

### 3. Two Columns
```yaml
- title: Comparaison
  layout: 2-columns
  content: |
    Colonne 1
    - Point A
    ---
    Colonne 2
    - Point B
```

### 4. Three Columns (fallback)
```yaml
- title: Trois Options
  layout: 3-columns
  content: |
    Option 1
    ---
    Option 2
    ---
    Option 3
```
**Note:** Utilise "Title and body" car pas de 3-col standard.

### 5. Two Panels
```yaml
- title: Section Title
  layout: 2-panels
  content: |
    Description de la section
```

## Options Avancées

### Dossier personnalisé
```bash
python3 tools/google-slides/generate_slides.py \
  --input file.slides.yaml \
  --folder-id "AUTRE_FOLDER_ID"
```

### Thème personnalisé
```bash
python3 tools/google-slides/generate_slides.py \
  --input file.slides.yaml \
  --template-id "AUTRE_TEMPLATE_ID"
```

Ou dans le YAML:
```yaml
title: Ma Présentation
template_id: "1ABC123..."

slides:
  - title: Slide 1
    layout: default
```

## Fichiers Exemples

- `example.slides.yaml` - Exemple basique
- `test-321-layouts.slides.yaml` - Test des layouts
- `agents/251031-greece-impact-venture-ideation/greece-impact-ventures.slides.yaml` - Exemple réel

## Limitations Connues

✅ **Supporté:**
- **Images markdown** - Upload automatique sur Google Drive avec syntaxe `![alt text](path/to/image.png)`
- 5 layouts natifs (default, hero, 2-columns, 3-columns, 2-panels)
- Template 321 theme appliqué automatiquement
- Multi-colonnes avec séparateur `---`

❌ **Pas encore supporté:**
- Layouts custom 321 (Quote, Thanks, 4-columns, etc.) via YAML
- Animations
- Notes de présentation
- Tableaux
- Positionnement custom des images

✅ **Workaround:**
1. Générer la présentation avec layouts de base
2. Ouvrir dans Google Slides
3. Changer manuellement les layouts custom si besoin

## Dépannage

### Erreur "File not found"
→ Le template ou dossier n'est pas partagé avec `memento-drive@agents-475314.iam.gserviceaccount.com`

### Erreur "Invalid layout"
→ Le layout demandé n'existe pas dans le template. Utilisez un des 5 layouts de base.

### Slides vides
→ Les placeholders du layout n'ont pas été trouvés. Vérifiez que le template a bien des placeholders TITLE et BODY.

## Support

Voir:
- `README.md` - Documentation technique
- `321-LAYOUTS.md` - Liste complète des layouts 321
- `.folders` - Configuration dossiers/template
