from django.shortcuts import render
from django.views.generic import DetailView, ListView

from .models import Category, Post


# Create your views here.
class blog_index(ListView):
    model = Post
    template_name = "blogpost_index.html"
    context_object_name = 'post'


class blog_Detail(DetailView):
    model = Post
    template_name = "blogpost_detail.html"
    context_object_name = 'post'
