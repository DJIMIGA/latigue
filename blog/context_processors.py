from .models import Post

post_processor = lambda request: {'posts': Post.objects.all()}
