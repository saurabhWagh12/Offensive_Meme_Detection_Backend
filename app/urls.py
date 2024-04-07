from django.contrib import admin
from django.urls import path
from .views import *
urlpatterns = [
    path('api/hate-speech/',HateSpeechAPI.as_view(),name='Hate-Speech'),
    path('api/get-comments/',CommentProcessing.as_view(),name='Comment-Processing'),
    path('api/purify/',WebPurify.as_view(),name='Image-Processing'),
]

