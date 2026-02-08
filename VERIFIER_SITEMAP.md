# Guide rapide : Vérifier et soumettre le sitemap

## 🔍 Étape 1 : Vérifier que le sitemap fonctionne

### En local (développement)
1. Démarrez le serveur :
   ```bash
   python manage.py runserver
   ```
2. Ouvrez dans votre navigateur :
   ```
   http://localhost:8000/sitemap.xml
   ```
3. Vous devriez voir un fichier XML avec toutes vos URLs

### En production
1. Ouvrez dans votre navigateur :
   ```
   https://bolibana.net/sitemap.xml
   ```

**Si ça ne fonctionne pas** :
- Vérifiez que le site est bien déployé sur Heroku
- Vérifiez les logs : `heroku logs --tail`
- Redéployez si nécessaire

---

## 📋 Étape 2 : Configurer Google Search Console

### 1. Créer un compte
- Allez sur : https://search.google.com/search-console
- Cliquez sur **"Démarrer"**
- Entrez : `bolibana.net` (sans https://)

### 2. Vérifier la propriété

**Méthode recommandée : DNS**
1. Google vous donne un enregistrement TXT
2. Ajoutez-le dans votre gestionnaire de DNS (chez votre registrar)
3. Cliquez sur **"Vérifier"**
4. Attendez quelques minutes

**Alternative : Fichier HTML**
1. Téléchargez le fichier HTML fourni par Google
2. Placez-le dans `static/`
3. Créez une route pour le servir (voir ci-dessous)

### 3. Soumettre le sitemap

Une fois vérifié :
1. Menu de gauche → **"Sitemaps"**
2. Dans **"Ajouter un nouveau sitemap"**, entrez :
   ```
   sitemap.xml
   ```
   (Juste `sitemap.xml`, pas l'URL complète)
3. Cliquez sur **"Envoyer"**

---

## 🔧 Si le sitemap ne fonctionne pas

### Vérifications à faire :

1. **Vérifier la route dans `latigue/urls.py`** :
   ```python
   path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
   ```

2. **Vérifier `INSTALLED_APPS` dans `settings.py`** :
   ```python
   'django.contrib.sitemaps',
   ```

3. **Vérifier que vous avez du contenu** :
   - Articles de blog
   - Services actifs
   - Formations actives

4. **Tester localement d'abord** :
   ```bash
   python manage.py runserver
   # Puis ouvrir http://localhost:8000/sitemap.xml
   ```

5. **Redéployer sur Heroku** :
   ```bash
   git add .
   git commit -m "Fix sitemap"
   git push heroku main
   ```

---

## 📝 Checklist rapide

- [ ] Le sitemap fonctionne en local (`http://localhost:8000/sitemap.xml`)
- [ ] Le sitemap est accessible en production (`https://bolibana.net/sitemap.xml`)
- [ ] Compte Google Search Console créé
- [ ] Propriété `bolibana.net` vérifiée (via DNS ou fichier HTML)
- [ ] Sitemap soumis dans Google Search Console (`sitemap.xml`)
- [ ] Statut "Réussi" dans Google Search Console (peut prendre quelques heures)

---

## 💡 Astuce

Si vous avez besoin de servir un fichier HTML pour la vérification Google :

1. Placez le fichier dans `static/google-verification.html`
2. Ajoutez dans `latigue/urls.py` :
   ```python
   from django.views.generic import TemplateView
   
   urlpatterns = [
       # ... vos autres routes
       path('google<votre-id>.html', TemplateView.as_view(template_name='google-verification.html')),
   ]
   ```

Mais la méthode DNS est plus simple et ne nécessite pas de code supplémentaire.


