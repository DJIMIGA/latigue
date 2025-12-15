# Dossier `blog/articles/`

Ce dossier contient les fichiers **Markdown** utilisés comme source pour les articles du blog.

## Comment l'utiliser avec Django

1. Rédigez ou mettez à jour un article en Markdown dans ce dossier  
   (ex. `GUIDE_GESTION_S3_DJANGO.md`).

2. Dans l’admin Django (`/admin/`) :
   - Allez dans **Blog → Posts**
   - Créez un nouvel article ou éditez-en un existant
   - Laissez le champ **`body`** vide (il sera rempli automatiquement)
   - Dans le champ **`markdown_file`**, uploadez le fichier `.md` correspondant

3. Enregistrer :
   - Le fichier est envoyé sur S3
   - Le contenu Markdown est converti en **HTML**
   - Le HTML est injecté dans le champ **`body`** de l’article

4. La page de détail du blog affiche ensuite `{{ post.body|safe }}` avec le style
   défini dans `templates/blog/blogpost_detail.html`.

## Bonnes pratiques

- Versionnez ces fichiers Markdown avec Git (comme ce projet)
- Donnez des noms explicites :
  - `GUIDE_GESTION_S3_DJANGO.md`
  - `INTRO_DJANGO_SIGNALS.md`
  - `TUTORIEL_DEPLOIEMENT_HEROKU.md`
- Utilisez les blocs de code avec langage pour profiter de la coloration :

```markdown
```bash
python manage.py collectstatic --noinput
```

```python
def example():
    print("Hello, world!")
```
```


