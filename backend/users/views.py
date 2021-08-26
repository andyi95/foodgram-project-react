"""Перенесли всю логику, связанную с пользователями в отдельный модуль."""
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from api.paginators import PageNumberPaginatorModified
from api.serializers import FollowReadSerializer

User = get_user_model()

class FollowReadViewSet(ReadOnlyModelViewSet):
    """Получить постраничный вывод подписок.

    Исходя из запросов, которые отправляет фронтенд, я сделал вывод, что
    во вложенной пагинации здесь нет необходимости: пагинируем авторов,
    на которых подписаны, а кол-во рецептов ограничивается сериализатором
    по запросу."""
    serializer_class = FollowReadSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPaginatorModified

    def get_queryset(self):
        qs = User.objects.follow_recipes(user=self.request.user).all()
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    # @method_decorator(vary_on_cookie)
    # @method_decorator(cache_page(CACHE_TIMEOUT))
    # def dispatch(self, request, *args, **kwargs):
    #     return super(FollowReadViewSet, self).dispatch(
    #         request, *args, **kwargs
    #     )