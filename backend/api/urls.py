from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.views import CustomUserViewSet
from .utils import ShoppingCardView
from .views import IngredientViewSet, RecipeViewSet, TagViewSet

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register('users', CustomUserViewSet, basename='users')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path(
        'recipes/download_shopping_cart/',
        ShoppingCardView.as_view(),
        name='download_shopping_cart'
    ),
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken'))
]
