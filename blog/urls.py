from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from blog.views import blog_Detail, blog_index, CategoryPostListView

urlpatterns = [path("", blog_index.as_view(), name="blog-index"),
               path('<slug:slug>/', blog_Detail.as_view(), name="blog-detail"),
               path('categorie/<slug:category_slug>/', CategoryPostListView.as_view(), name="category-posts"),
               ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL,
                                                                                            document_root=settings.MEDIA_ROOT
                                                                                            )
