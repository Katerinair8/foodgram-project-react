from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

import io

from django.db.models import Sum
from django.http import FileResponse
from rest_framework.views import APIView
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .filters import IngredientFilter, RecipeFilter
from .mixins import ListRetrieveViewSet
from users.models import Subscribe
from .pagination import CustomPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from recipes.models import Favorite, Ingredient, Recipe, Shopping, Tag, RecipeIngredient
from .serializers import (FollowSerializer, IngredientSerializer, RecipeFollowSerializer,
                          RecipeGetSerializer, RecipeSerializer, TagSerializer)
from .utils import delete, post

from .constants import *

CustomUser = get_user_model()

class CustomUserViewSet(UserViewSet):
    pagination_class = CustomPageNumberPagination

    @action(
        detail=True,
        permission_classes=[IsAuthenticated],
        methods=['POST', 'DELETE']
    )
    def subscribe(self, request, id=None):
        current_user = request.user
        author = get_object_or_404(CustomUser, id=id)
        if self.request.method == 'POST':
            if Subscribe.objects.filter(user=current_user, author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на данного пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if current_user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow = Subscribe.objects.create(user=current_user, author=author)
            serializer = FollowSerializer(
                follow, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif self.request.method == 'DELETE':
            if Subscribe.objects.filter(user=current_user, author=author).exists():
                follow = get_object_or_404(Subscribe, user=current_user, author=author)
                follow.delete()
                return Response(
                    'Подписка успешно удалена',
                    status=status.HTTP_204_NO_CONTENT
                )
            if current_user == author:
                return Response(
                    {'errors': 'Нельзя отписаться от самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'errors': 'Вы не подписаны на данного пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False,
        permission_classes=[IsAuthenticated],
        methods=['GET']
    )
    def subscriptions(self, request):
        user = request.user
        queryset = Subscribe.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(ListRetrieveViewSet):
    """Класс представления тега."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(ListRetrieveViewSet):
    """Класс представления ингредиента."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Класс представления рецептов."""

    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited is not None and int(is_favorited) == 1:
            return Recipe.objects.filter(favorites__user=self.request.user)
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        if is_in_shopping_cart is not None and int(is_in_shopping_cart) == 1:
            return Recipe.objects.filter(cart__user=self.request.user)
        return Recipe.objects.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeGetSerializer
        return RecipeSerializer

    def get_permissions(self):
        if self.action != 'create':
            return(IsAuthorOrReadOnly(),)
        return super().get_permissions()

    @action(detail=True, methods=['POST', 'DELETE'],)
    def favorite(self, request, pk):
        if request.method == 'POST':
            return post(request, pk, Favorite, RecipeFollowSerializer)
        elif request.method == 'DELETE':
            return delete(request, pk, Favorite)

    @action(detail=True, methods=['POST', 'DELETE'],)
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return post(request, pk, Shopping, RecipeFollowSerializer)
        elif request.method == 'DELETE':
            return delete(request, pk, Shopping)



class ShoppingCardView(APIView):
    """Класс представления списка покупок."""

    def get(self, request):
        user = request.user
        shopping_list = RecipeIngredient.objects.filter(
            recipe__cart__user=user).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            amount=Sum('amount')
        ).order_by()
        font = PDF_FONT_NAME
        pdfmetrics.registerFont(
            TTFont(PDF_FONT_NAME, f'{PDF_FONT_NAME}.ttf', 'UTF-8')
        )
        buffer = io.BytesIO()
        pdf_file = canvas.Canvas(buffer)
        pdf_file.setFont(font, PDF_HEADER_FONT_SIZE)
        pdf_file.drawString(
            PDF_CENTER,
            PDF_HEIGHT,
            PDF_HEADER_TEXT,
        )
        pdf_file.setFont(font, PDF_TEXT_FONT_SIZE)
        from_bottom = PDF_HEIGHT - PDF_LEFT
        for number, ingredient in enumerate(shopping_list, start=1):
            pdf_file.drawString(
                PDF_LEFT,
                from_bottom,
                (f'{number}.  {ingredient["ingredient__name"]} - '
                 f'{ingredient["amount"]} '
                 f'{ingredient["ingredient__measurement_unit"]}')
            )
            from_bottom -= PDF_STEP
            if from_bottom <= PDF_LEFT:
                from_bottom = PDF_HEIGHT
                pdf_file.showPage()
                pdf_file.setFont(font, PDF_TEXT_FONT_SIZE)
        pdf_file.showPage()
        pdf_file.save()
        buffer.seek(0)
        return FileResponse(
            buffer, as_attachment=True, filename=PDF_FILENAME
        )
    
    