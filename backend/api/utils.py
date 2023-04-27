from typing import Union

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from recipes.models import Favorite, Recipe, RecipeIngredient, Shopping


def prepare_post_response(
    request: Request,
    pk: int,
    model: Union[Favorite, Shopping],
    serializer: Serializer,
    error_message: str,
) -> Response:
    recipe = get_object_or_404(Recipe, pk=pk)
    if model.objects.filter(user=request.user, recipe=recipe).exists():
        return Response(
            {"errors": error_message},
            status=status.HTTP_400_BAD_REQUEST,
        )
    model.objects.get_or_create(user=request.user, recipe=recipe)
    data = serializer(recipe).data
    return Response(data, status=status.HTTP_201_CREATED)


def prepare_delete_response(
    request: Request,
    pk: int,
    model: Union[Favorite, Shopping],
    success_message: str,
    not_found_message: str,
) -> Response:
    recipe = get_object_or_404(Recipe, pk=pk)
    if model.objects.filter(user=request.user, recipe=recipe).exists():
        follow = get_object_or_404(model, user=request.user, recipe=recipe)
        follow.delete()
        return Response(
            success_message,
            status=status.HTTP_204_NO_CONTENT,
        )
    return Response(
        {"errors": not_found_message},
        status=status.HTTP_400_BAD_REQUEST,
    )


def recipe_ingredient_create(
    ingredients_data, model: RecipeIngredient, recipe: Recipe
) -> None:
    bulk_create_data = [
        model(
            recipe=recipe,
            ingredient=ingredient_data["ingredient"],
            amount=ingredient_data["amount"],
        )
        for ingredient_data in ingredients_data
    ]
    model.objects.bulk_create(bulk_create_data)
