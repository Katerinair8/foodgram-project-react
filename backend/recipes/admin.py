from django.conf import settings
from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient, Shopping,
                     Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    search_fields = ('name', 'color', 'slug')
    list_filter = ('name', 'color', 'slug',)
    ordering = ('name',)
    empty_value_display = settings.EMPTY_VALUE_DISPLAY


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('name',)
    ordering = ('id',)
    empty_value_display = settings.EMPTY_VALUE_DISPLAY


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'count_favorites')
    search_fields = ('username', 'email', 'first_name', 'last_name',)
    list_filter = ('author', 'name', 'tags',)
    ordering = ('name',)
    empty_value_display = settings.EMPTY_VALUE_DISPLAY

    def count_favorites(self, obj):
        return obj.favorites.count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe', 'ingredient',)
    list_filter = ('recipe', 'ingredient',)
    empty_value_display = settings.EMPTY_VALUE_DISPLAY


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user', 'recipe',)
    list_filter = ('user', 'recipe',)
    empty_value_display = settings.EMPTY_VALUE_DISPLAY


@admin.register(Shopping)
class ShoppingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user', 'recipe',)
    list_filter = ('user', 'recipe',)
    empty_value_display = settings.EMPTY_VALUE_DISPLAY
