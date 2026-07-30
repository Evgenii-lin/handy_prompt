"""URL configuration for prompt_website project."""
from django.contrib import admin
from django.urls import path
from prompt_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.main_page, name='main_page'),
    path('new_prompt/', views.new_prompt, name='new_prompt'),
    path('load_prompt/<int:prompt_id>/', views.load_prompt, name='load_prompt'),
    path('copy_text/<int:prompt_id>/', views.copy_text, name='copy_text'),
    path('edit_prompt/<int:prompt_id>/', views.edit_prompt, name='edit_prompt'),
    path('delete_prompt/<int:prompt_id>/', views.delete_prompt, name='delete_prompt'),
    path('cleanup_duplicates/', views.cleanup_duplicates, name='cleanup_duplicates'),
    path('extract_prompt/', views.extract_prompt, name='extract_prompt'),
    path('extract_all_prompts/', views.extract_all_prompts, name='extract_all_prompts'),
]
