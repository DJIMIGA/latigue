from django.urls import path
from . import views
from . import webhook

app_name = 'chatbot'

urlpatterns = [
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/webhook/github/', webhook.github_webhook, name='github_webhook'),
]
