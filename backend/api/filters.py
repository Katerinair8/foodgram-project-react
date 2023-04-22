import django_filters
from django.contrib.auth import get_user_model

from recipes.models import Ingredient, Recipe, Tag

User = get_user_model()


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name', 'measurement_unit')


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    author = django_filters.ModelChoiceFilter(queryset=User.objects.all())

    # обе переменные берутся из  query_params запроса  Как их брать в фильтре? и как отфильтровать по юзеру?

    # is_favorited = django_filters.BooleanFilter(
    #     field_name=request.is_favorited,
    #     queryset=Recipe.objects.filter(favorites__user=request.user),
    # )

    # is_in_shopping_cart = django_filters.BooleanFilter(
    #     field_name='is_favorited',
    #     queryset=Recipe.objects.filter(cart__user=request.user),
    # )

    class Meta:
        model = Recipe
        fields = ('tags', 'author')
