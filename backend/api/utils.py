import io

from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import Recipe, RecipeIngredient


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
        font = 'Tantular'
        pdfmetrics.registerFont(
            TTFont('Tantular', 'Tantular.ttf', 'UTF-8')
        )
        buffer = io.BytesIO()
        pdf_file = canvas.Canvas(buffer)
        pdf_file.setFont(font, 24)
        pdf_file.drawString(
            150,
            800,
            'Список покупок:'
        )
        pdf_file.setFont(font, 14)
        from_bottom = 750
        for number, ingredient in enumerate(shopping_list, start=1):
            pdf_file.drawString(
                50,
                from_bottom,
                (f'{number}.  {ingredient["ingredient__name"]} - '
                 f'{ingredient["amount"]} '
                 f'{ingredient["ingredient__measurement_unit"]}')
            )
            from_bottom -= 20
            if from_bottom <= 50:
                from_bottom = 800
                pdf_file.showPage()
                pdf_file.setFont(font, 14)
        pdf_file.showPage()
        pdf_file.save()
        buffer.seek(0)
        return FileResponse(
            buffer, as_attachment=True, filename='shopping_list.pdf'
        )


def post(request, pk, model, serializer):
    recipe = get_object_or_404(Recipe, pk=pk)
    if model.objects.filter(user=request.user, recipe=recipe).exists():
        return Response(
            {'errors': 'Рецепт уже есть в избранном/списке покупок'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    model.objects.get_or_create(user=request.user, recipe=recipe)
    data = serializer(recipe).data
    return Response(data, status=status.HTTP_201_CREATED)


def delete(request, pk, model):
    recipe = get_object_or_404(Recipe, pk=pk)
    if model.objects.filter(user=request.user, recipe=recipe).exists():
        follow = get_object_or_404(model, user=request.user,
                                   recipe=recipe)
        follow.delete()
        return Response(
            'Рецепт успешно удален из избранного/списка покупок',
            status=status.HTTP_204_NO_CONTENT
        )
    return Response(
        {'errors': 'Данного рецепта не было в избранном/списке покупок'},
        status=status.HTTP_400_BAD_REQUEST
    )


def recipe_ingredient_create(ingredients_data, models, recipe):
    bulk_create_data = (
        models(
            recipe=recipe,
            ingredient=ingredient_data['ingredient'],
            amount=ingredient_data['amount'])
        for ingredient_data in ingredients_data
    )
    models.objects.bulk_create(bulk_create_data)
