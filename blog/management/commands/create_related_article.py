from django.core.management.base import BaseCommand
from blog.models import Post, Category
from django.utils import timezone

class Command(BaseCommand):
    help = "Crée un article de blog sur le système related dans Django"

    def handle(self, *args, **options):
        # Créer ou récupérer la catégorie
        category, _ = Category.objects.get_or_create(name='Django')

        article_content = '''
<h2>Comprendre le système <code>related</code> dans Django</h2>

<p>Le système <strong>related</strong> de Django permet de naviguer facilement dans les relations entre modèles, que ce soit en base de données ou dans les templates. Il s'appuie principalement sur l'option <code>related_name</code> des champs relationnels (<code>ForeignKey</code>, <code>ManyToManyField</code>, etc.).</p>

<h3>1. Déclaration dans le modèle</h3>
<pre><code class="language-python">class Category(models.Model):
    name = models.CharField(max_length=50)

class Post(models.Model):
    title = models.CharField(max_length=200)
    categories = models.ManyToManyField(Category, related_name="posts")
</code></pre>

<p>Ici, <code>related_name="posts"</code> permet d'accéder à tous les articles d'une catégorie via <code>ma_categorie.posts.all()</code>.</p>

<h3>2. Utilisation côté Python</h3>
<ul>
<li><strong>Depuis un Post</strong> : <code>post.categories.all()</code> (catégories de l'article)</li>
<li><strong>Depuis une Category</strong> : <code>category.posts.all()</code> (tous les articles de cette catégorie)</li>
</ul>

<h3>3. Utilisation dans un template</h3>
<pre><code class="language-django">{% raw %}{% for post in category.posts.all %}
  {{ post.title }}
{% endfor %}{% endraw %}</code></pre>

<h3>4. Utilisation dans une vue</h3>
<pre><code class="language-python">category = Category.objects.get(slug="django")
articles = category.posts.all()  # grâce à related_name="posts"
</code></pre>

<h3>5. Avantages</h3>
<ul>
<li>Navigation simple et intuitive dans les relations</li>
<li>Nommer la relation inverse comme on veut</li>
<li>Requêtes croisées et filtres facilités</li>
</ul>

<h3>Résumé</h3>
<p>Le système <code>related</code> de Django rend la gestion des relations entre modèles puissante et élégante, aussi bien côté Python que dans les templates. Utilisez toujours <code>related_name</code> pour des relations claires et un code maintenable !</p>
'''

        post, created = Post.objects.get_or_create(
            title="Le système related dans Django",
            defaults={
                'body': article_content,
                'created_on': timezone.now(),
            }
        )
        if created:
            post.categories.add(category)
            self.stdout.write(self.style.SUCCESS('✅ Article "Le système related dans Django" créé avec succès !'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ L\'article existe déjà.')) 