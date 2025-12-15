# Guide Google Search Console - Configuration du Sitemap

## 🔍 Vérification du sitemap

### 1. Tester le sitemap localement

D'abord, vérifiez que le sitemap fonctionne en local :

```bash
# Démarrer le serveur de développement
python manage.py runserver

# Tester l'URL
http://localhost:8000/sitemap.xml
```

Le sitemap devrait s'afficher en XML avec toutes vos URLs.

### 2. Vérifier en production

Testez l'URL en production :
- **URL à tester** : `https://bolibana.net/sitemap.xml`

**Si le sitemap ne s'affiche pas** :

#### Causes possibles :
1. **Le site n'est pas déployé** : Vérifiez que les dernières modifications sont sur Heroku
2. **Problème de configuration** : Vérifiez que `django.contrib.sitemaps` est dans `INSTALLED_APPS`
3. **Problème de route** : Vérifiez que la route est bien dans `urls.py`

#### Solution rapide :
```bash
# Sur Heroku, vérifiez les logs
heroku logs --tail

# Redéployez si nécessaire
git add .
git commit -m "Fix sitemap configuration"
git push heroku main
```

---

## 📋 Configuration Google Search Console

### Étape 1 : Créer un compte Google Search Console

1. Allez sur : https://search.google.com/search-console
2. Cliquez sur **"Démarrer"**
3. Entrez votre propriété : `https://bolibana.net` (ou `bolibana.net`)

### Étape 2 : Vérifier la propriété

Vous avez plusieurs options pour vérifier :

#### Option A : Méthode HTML (recommandée)
1. Google vous donne un fichier HTML à télécharger
2. Placez-le dans votre dossier `static/`
3. Ajoutez une route dans `urls.py` :

```python
# Dans portfolio/urls.py ou latigue/urls.py
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... vos autres routes
    path('google<id>.html', TemplateView.as_view(template_name='google-verification.html'), name='google-verification'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

#### Option B : Méthode DNS (plus simple)
1. Google vous donne un enregistrement TXT à ajouter
2. Ajoutez-le dans votre gestionnaire de DNS (chez votre registrar)
3. Attendez la propagation DNS (quelques minutes à quelques heures)

#### Option C : Méthode Google Analytics (si vous avez GA)
1. Si vous avez déjà Google Analytics configuré
2. Google peut utiliser cette connexion pour vérifier

### Étape 3 : Soumettre le sitemap

Une fois la propriété vérifiée :

1. Dans Google Search Console, allez dans **"Sitemaps"** (menu de gauche)
2. Dans le champ **"Ajouter un nouveau sitemap"**, entrez :
   ```
   sitemap.xml
   ```
   (Juste `sitemap.xml`, pas l'URL complète)
3. Cliquez sur **"Envoyer"**

### Étape 4 : Vérifier le statut

Après quelques minutes/heures :
- Le statut devrait passer à **"Réussi"**
- Vous verrez le nombre d'URLs découvertes

---

## 🔧 Dépannage

### Problème : "Impossible d'extraire le sitemap"

**Solutions** :
1. Vérifiez que `https://bolibana.net/sitemap.xml` est accessible dans un navigateur
2. Vérifiez que le sitemap est bien formaté (XML valide)
3. Vérifiez les logs Heroku pour des erreurs

### Problème : "Sitemap vide"

**Solutions** :
1. Vérifiez que vous avez des articles/services/formations dans la base de données
2. Vérifiez que les modèles retournent bien des objets dans `items()`
3. Testez localement avec `python manage.py shell` :

```python
from blog.models import Post
from services.models import Service
from formations.models import Formation

# Vérifier que vous avez des données
print(f"Posts: {Post.objects.count()}")
print(f"Services: {Service.objects.filter(is_active=True).count()}")
print(f"Formations: {Formation.objects.filter(is_active=True).count()}")
```

### Problème : "Erreur 404"

**Solutions** :
1. Vérifiez que la route est bien dans `latigue/urls.py` :
   ```python
   path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
   ```
2. Vérifiez que `django.contrib.sitemaps` est dans `INSTALLED_APPS`
3. Redéployez sur Heroku

---

## 📊 Vérification du sitemap

### Test manuel

Ouvrez dans votre navigateur :
```
https://bolibana.net/sitemap.xml
```

Vous devriez voir un XML avec :
- Des URLs de pages statiques
- Des URLs d'articles de blog
- Des URLs de catégories
- Des URLs de services
- Des URLs de formations

### Test avec curl (terminal)

```bash
curl https://bolibana.net/sitemap.xml
```

### Test avec un validateur

Utilisez un validateur de sitemap en ligne :
- https://www.xml-sitemaps.com/validate-xml-sitemap.html
- Collez l'URL : `https://bolibana.net/sitemap.xml`

---

## 🚀 Checklist complète

- [ ] Le sitemap fonctionne en local (`http://localhost:8000/sitemap.xml`)
- [ ] Le sitemap est accessible en production (`https://bolibana.net/sitemap.xml`)
- [ ] Compte Google Search Console créé
- [ ] Propriété `bolibana.net` vérifiée
- [ ] Sitemap soumis dans Google Search Console
- [ ] Statut "Réussi" dans Google Search Console
- [ ] URLs découvertes > 0

---

## 📝 Notes importantes

1. **Temps de traitement** : Google peut prendre quelques heures à quelques jours pour traiter le sitemap
2. **Mise à jour automatique** : Le sitemap se met à jour automatiquement quand vous ajoutez du contenu
3. **Resoumission** : Pas besoin de resoumettre le sitemap, Google le vérifie régulièrement
4. **Plusieurs sitemaps** : Vous pouvez créer des sitemaps séparés si vous avez beaucoup d'URLs (>50,000)

---

## 🔗 Ressources utiles

- [Google Search Console](https://search.google.com/search-console)
- [Documentation Django Sitemaps](https://docs.djangoproject.com/en/stable/ref/contrib/sitemaps/)
- [Guide Google sur les sitemaps](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview)

---

## 💡 Astuce

Si le sitemap ne fonctionne toujours pas après vérification, créez un fichier de test simple pour vérifier que les routes fonctionnent :

```python
# Dans latigue/urls.py, ajoutez temporairement :
from django.http import HttpResponse

def test_sitemap(request):
    return HttpResponse("Sitemap test OK", content_type="text/plain")

urlpatterns = [
    # ...
    path('test-sitemap', test_sitemap, name='test-sitemap'),
]
```

Puis testez : `https://bolibana.net/test-sitemap`

