from django.core.management.base import BaseCommand
from blog.models import Post, Category
from django.utils import timezone

class Command(BaseCommand):
    help = 'Crée un article de blog sur la redirection www vers non-www'

    def handle(self, *args, **options):
        # Créer ou récupérer une catégorie
        category, created = Category.objects.get_or_create(name='Développement Web')
        
        # Contenu de l'article avec le bon formatage HTML
        article_content = '''
<h2>Redirection de www vers non-www (ou l'inverse) sur Django & Heroku</h2>

<p>Pour garantir une expérience utilisateur cohérente et améliorer le référencement, il est recommandé de choisir une version principale de votre domaine (avec ou sans <strong>www</strong>) et de rediriger automatiquement l'autre vers celle-ci.</p>

<h3>Pourquoi faire cette redirection ?</h3>
<ul>
    <li>Éviter le contenu dupliqué pour Google</li>
    <li>Améliorer la cohérence de marque</li>
    <li>Centraliser les statistiques d'audience</li>
    <li>Optimiser le SEO</li>
</ul>

<h3>Configuration DNS chez Gandi</h3>
<p>Voici la configuration recommandée pour votre domaine :</p>
<ul>
    <li><strong>www.bolibana.net</strong> : CNAME vers <code>cubed-parasaurolophus-3z5g995zs6sbrb042nmfip48.herokudns.com</code></li>
    <li><strong>bolibana.net</strong> : A record vers <code>76.76.21.21</code> (IP Heroku pour l'apex)</li>
</ul>

<h3>Ajouter les domaines sur Heroku</h3>
<p>Exécutez ces commandes dans votre terminal :</p>
<pre><code>heroku domains:add bolibana.net
heroku domains:add www.bolibana.net</code></pre>

<h3>Redirection automatique dans Django</h3>
<p>Pour forcer la redirection de <strong>www</strong> vers non-www (ou l'inverse), ajoutez ce middleware dans votre projet :</p>

<pre><code class="language-python"># middleware.py
from django.http import HttpResponsePermanentRedirect

class WwwRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        if host.startswith('www.'):
            return HttpResponsePermanentRedirect(
                request.build_absolute_uri().replace('://www.', '://', 1)
            )
        return self.get_response(request)</code></pre>

<p>Ajoutez-le dans <code>settings.py</code> juste après les middlewares de sécurité :</p>
<pre><code>MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # ...
    'votre_app.middleware.WwwRedirectMiddleware',
    # ...
]</code></pre>

<h3>Configuration dans ALLOWED_HOSTS</h3>
<p>Assurez-vous d'avoir les deux versions dans vos paramètres Django :</p>
<pre><code>ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.herokuapp.com',
    'bolibana.net',
    'www.bolibana.net',
]</code></pre>

<h3>Vérification de la propagation DNS</h3>
<p>Après avoir modifié les enregistrements DNS, utilisez cette commande pour vérifier que tout fonctionne :</p>
<pre><code>heroku domains:wait bolibana.net</code></pre>

<h3>Avantages de cette approche</h3>
<ul>
    <li><strong>SEO optimisé</strong> : Évite le contenu dupliqué</li>
    <li><strong>UX cohérente</strong> : Les utilisateurs arrivent toujours au bon endroit</li>
    <li><strong>Maintenance simplifiée</strong> : Une seule version à gérer</li>
    <li><strong>Statistiques unifiées</strong> : Toutes les visites sont centralisées</li>
</ul>

<h3>Conclusion</h3>
<p>En combinant une bonne configuration DNS, l'ajout des domaines sur Heroku et un middleware Django, vous garantissez que vos visiteurs arrivent toujours sur la bonne version de votre site. Cette approche est bénéfique pour l'image de marque et le référencement naturel.</p>

<p><em>Note : La propagation DNS peut prendre jusqu'à 24 heures, mais elle est généralement effective en quelques minutes.</em></p>
        '''

        # Créer l'article
        post, created = Post.objects.get_or_create(
            title="Redirection de www vers non-www (ou l'inverse) sur Django & Heroku",
            defaults={
                'body': article_content,
                'created_on': timezone.now(),
            }
        )
        
        if created:
            post.categories.add(category)
            self.stdout.write(
                self.style.SUCCESS('✅ Article créé avec succès !')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️ L\'article existe déjà.')
            ) 