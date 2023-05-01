import io

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView

from api.constants import (PDF_CENTER, PDF_FILENAME, PDF_FONT_NAME,
                           PDF_HEADER_FONT_SIZE, PDF_HEADER_TEXT, PDF_HEIGHT,
                           PDF_LEFT, PDF_STEP, PDF_TEXT_FONT_SIZE)
from api.filters import IngredientFilter, RecipeFilter
from api.mixins import ListRetrieveViewSet
from api.pagination import CustomPageNumberPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (FollowSerializer, IngredientSerializer,
                             RecipeFollowSerializer, RecipeGetSerializer,
                             RecipeSerializer, TagSerializer)
from api.utils import prepare_delete_response, prepare_post_response
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            Shopping, Tag)
from users.models import Subscribe

CustomUser = get_user_model()


class CustomUserViewSet(UserViewSet):
    pagination_class = CustomPageNumberPagination

    @action(
        detail=True,
        permission_classes=[IsAuthenticated],
        methods=["POST", "DELETE"],
    )
    def subscribe(self, request, id=None):
        current_user = request.user
        author = get_object_or_404(CustomUser, id=id)
        context = {"request": request, "user": current_user, "author": author}

        serializer = FollowSerializer(
            data=dict(),
            context=context,
        )

        serializer.is_valid(raise_exception=True)

        if self.request.method == "POST":
            follow = Subscribe.objects.create(user=current_user, author=author)
            serializer = FollowSerializer(follow, context=context)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif self.request.method == "DELETE":
            follow = get_object_or_404(
                Subscribe,
                user=current_user,
                author=author,
            )
            follow.delete()
            return Response(
                "Подписка успешно удалена",
                status=status.HTTP_204_NO_CONTENT,
            )

    @action(
        detail=False,
        permission_classes=[IsAuthenticatedOrReadOnly],
        methods=["GET"],
    )
    def subscriptions(self, request):
        current_user = request.user
        context = {"request": request, "user": current_user, "author": None}
        queryset = Subscribe.objects.filter(user=current_user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(pages, many=True, context=context)
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

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return RecipeGetSerializer
        return RecipeSerializer

    def get_permissions(self):
        if self.action != "create":
            return (IsAuthorOrReadOnly(),)
        return super().get_permissions()

    @action(
        detail=True,
        methods=["POST", "DELETE"],
    )
    def favorite(self, request, pk):
        if request.method == "POST":
            return prepare_post_response(
                request=request,
                pk=pk,
                model=Favorite,
                serializer=RecipeFollowSerializer,
                error_message="Рецепт уже есть в избранном",
            )
        elif request.method == "DELETE":
            return prepare_delete_response(
                request=request,
                pk=pk,
                model=Favorite,
                success_message="Рецепт успешно удален из избранного",
                not_found_message="Данного рецепта не было в избранном",
            )

    @action(
        detail=True,
        methods=["POST", "DELETE"],
    )
    def shopping_cart(self, request, pk):
        if request.method == "POST":
            return prepare_post_response(
                request=request,
                pk=pk,
                model=Shopping,
                serializer=RecipeFollowSerializer,
                error_message="Рецепт уже есть в списке покупок",
            )
        elif request.method == "DELETE":
            return prepare_delete_response(
                request=request,
                pk=pk,
                model=Shopping,
                success_message="Рецепт успешно удален из списка покупок",
                not_found_message="Данного рецепта не было в списке покупок",
            )


class ShoppingCardView(APIView):
    """Класс представления списка покупок."""

    def get(self, request):
        user = request.user
        shopping_list = (
            RecipeIngredient.objects.filter(recipe__cart__user=user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(amount=Sum("amount"))
            .order_by()
        )
        pdfmetrics.registerFont(
            TTFont(
                PDF_FONT_NAME,
                f"{PDF_FONT_NAME}.ttf",
                "UTF-8",
            )
        )
        buffer = io.BytesIO()
        pdf_file = canvas.Canvas(buffer)
        pdf_file.setFont(PDF_FONT_NAME, PDF_HEADER_FONT_SIZE)
        pdf_file.drawString(
            PDF_CENTER,
            PDF_HEIGHT,
            PDF_HEADER_TEXT,
        )
        pdf_file.setFont(PDF_FONT_NAME, PDF_TEXT_FONT_SIZE)
        from_bottom = PDF_HEIGHT - PDF_LEFT
        for number, ingredient in enumerate(shopping_list, start=1):
            pdf_file.drawString(
                PDF_LEFT,
                from_bottom,
                (
                    f'{number}.  {ingredient["ingredient__name"]} - '
                    f'{ingredient["amount"]} '
                    f'{ingredient["ingredient__measurement_unit"]}'
                ),
            )
            from_bottom -= PDF_STEP
            if from_bottom <= PDF_LEFT:
                from_bottom = PDF_HEIGHT
                pdf_file.showPage()
                pdf_file.setFont(PDF_FONT_NAME, PDF_TEXT_FONT_SIZE)
        pdf_file.showPage()
        pdf_file.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=PDF_FILENAME)
