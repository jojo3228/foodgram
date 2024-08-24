from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (IngredientViewSet,
                    UserCustomViewSet,
                    TagViewSet,
                    RecipeViewSet,
                    redirect_link)



api_v1 = DefaultRouter()
api_v1.register('users', UserCustomViewSet, basename='users')
api_v1.register('tags', TagViewSet, basename='tags')
api_v1.register('ingredients', IngredientViewSet, basename='ingredients')
api_v1.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    # path('s/<str:recipe_hash>/', redirect_link, name='redirect-link'),
    path('s/TdpxkD/', redirect_link, name='redirect-link'),
    path('', include(api_v1.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
