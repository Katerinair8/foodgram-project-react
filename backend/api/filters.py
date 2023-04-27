import django_filters
from django.contrib.auth import get_user_model

from recipes.models import Ingredient, Recipe, Tag

User = get_user_model()


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name="name",
        lookup_expr="istartswith",
    )

    class Meta:
        model = Ingredient
        fields = ("name", "measurement_unit")


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
    )
    author = django_filters.ModelChoiceFilter(queryset=User.objects.all())

    is_favorited = django_filters.BooleanFilter(
        method="is_favorited",
    )

    is_in_shopping_cart = django_filters.BooleanFilter(
        method="is_in_shopping_cart",
    )

    class Meta:
        model = Recipe
        fields = ("tags", "author")

    def is_favorited(self, queryset, name, value, request):
        if value:
            return queryset.filter(favorites__user=request.user)
        return queryset

    def is_in_shopping_cart(self, queryset, name, value, request):
        if value:
            return queryset.filter(cart__user=request.user)
        return queryset
