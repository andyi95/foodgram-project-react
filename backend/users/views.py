"""Move user's logic to the appropriate app."""
from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from api.models import Follow
from api.paginators import PageNumberPaginatorModified
from api.permissions import IsOwnerOrReadOnly
from users.serializers import (FollowReadSerializer, FollowSerializer,
                               UserSerializer)

User = get_user_model()


class FollowReadViewSet(ReadOnlyModelViewSet):
    """Get paginated list of user's subscriptions.

    According to the frontend requests I came to conclusion that the nested
    pagination won't be necessary here: we have just to paginate subscribed
    user lists and the recipes-per-user amount will be restricted with the
    serializer by query parameter 'limit_recipes'.
    """

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


class AuthorViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class FollowViewSet(APIView):
    permission_classes = [IsOwnerOrReadOnly]

    def get(self, request, author_id):
        user = request.user
        data = {
            'user': user.id,
            'author': author_id
        }
        serializer = FollowSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, author_id):
        user = request.user
        follow = get_object_or_404(
            Follow, user_id=user.id, author_id=author_id
        )
        follow.delete()
        return Response('Вы успешно отписаны',
                        status=status.HTTP_204_NO_CONTENT)
