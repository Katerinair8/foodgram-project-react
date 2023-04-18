from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.pagination import CustomPageNumberPagination
from api.serializers import FollowSerializer
from .models import Subscribe

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    pagination_class = CustomPageNumberPagination

    @action(
        detail=True,
        permission_classes=[IsAuthenticated],
        methods=['POST', 'DELETE']
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if self.request.method == 'POST':
            if Subscribe.objects.filter(user=user, author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на данного пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow = Subscribe.objects.create(user=user, author=author)
            serializer = FollowSerializer(
                follow, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if Subscribe.objects.filter(user=user, author=author).exists():
            follow = get_object_or_404(Subscribe, user=user, author=author)
            follow.delete()
            return Response(
                'Подписка успешно удалена',
                status=status.HTTP_204_NO_CONTENT
            )
        if user == author:
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
