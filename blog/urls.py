from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from blog.views import blog_Detail, blog_index

urlpatterns = [path("blog/", blog_index.as_view(), name="blog-index"),
               path('<int:pk>', blog_Detail.as_view(), name="blog-detail"),
               ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL,
                                                                                            document_root=settings.MEDIA_ROOT
                                                                                            )
