from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Home page
        path('country-news/', views.country_list, name='country_list'),
    path('country-news/<str:country_code>/', views.country_news, name='country_news'),
    path('college-news/', views.college_news, name='college_news'),  # College news page
    path('category/<str:category_name>/', views.category_news, name='category_news'),
     path('nearby-news/', views.nearby_news, name='nearby_news'),
     path('auth/', views.auth_view, name='auth'), 
     path('my-articles/', views.user_articles, name='user_articles'),
    path('bookmarks/', views.bookmarks, name='bookmarks'),
    path('general_news_json/', views.general_news_json, name='general_news_json'),
    path('college-news-json/', views.college_news_json, name='college_news_json'),
    path('terms/', views.terms_view, name='terms'),
    ]
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)