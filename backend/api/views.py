from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser import views
from foodgram_api import settings
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from api.filters import RecipeFilter
from api.models import (FavorRecipes, Follow, Ingredient, Recipe,
                        RecipeComponent, ShoppingList, Tag, User)
from api.permissions import IsOwnerOrReadOnly
from api.serializers import (
    FavorSerializer, IngredientSerializer,
    ListFollowerSerializer, ListSubscriptionsSerializer, NewRecipeSerializer,
    RecipeSerializer, ShoppingSerializer,
    TagSerializer, UserSerializer
)


class GetPostViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                     mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    pass


class GetPostDelViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                        mixins.RetrieveModelMixin, mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    pass


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_class = RecipeFilter
    permission_classes = [IsOwnerOrReadOnly, ]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeSerializer
        return NewRecipeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny, )
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', ]


class FavoriteViewSet(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, recipe_id):
        user = request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if FavorRecipes.objects.filter(author=user, recipes=recipe).exists():
            return Response(
                'The object exists already',
                status=status.HTTP_400_BAD_REQUEST)
        FavorRecipes.objects.create(author=user, recipes=recipe)
        serializer = FavorSerializer(recipe)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED)

    def delete(self, request, recipe_id):
        user = request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        favorite_obj = get_object_or_404(FavorRecipes, user=user, recipe=recipe)
        if not favorite_obj:
            return Response(
                'The recipe has not been favorited',
                status=status.HTTP_400_BAD_REQUEST)
        favorite_obj.delete()
        return Response(
            'Removed', status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)



class ShoppingViewSet(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ShoppingSerializer

    def get(self, request, recipe_id):
        user = request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        ShoppingList.objects.create(user=user, recipe=recipe)
        serializer = FavorSerializer(recipe)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED)

    def delete(self, request, recipe_id):
        user = request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        shopping_list_obj = get_object_or_404(
            ShoppingList, user=user, recipe=recipe)
        shopping_list_obj.delete()
        return Response(
            'Deleted', status=status.HTTP_204_NO_CONTENT)


class AuthorViewSet(views.UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class FollowViewSet(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, author_id):
        user = request.user
        author = get_object_or_404(User, id=author_id)
        if Follow.objects.filter(user=user, author=author).exists():
            return Response(
                'Subscribed',
                status=status.HTTP_400_BAD_REQUEST)
        Follow.objects.create(user=user, author=author)
        serializer = UserSerializer(author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        user = request.user
        author = get_object_or_404(User, id=user_id)
        follow = get_object_or_404(Follow, user=user, author=author)
        follow.delete()
        return Response('Unsubscribed',
                        status=status.HTTP_204_NO_CONTENT)


class FollowListViewSet(ModelViewSet):
    serializer_class = ListFollowerSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        ps = Recipe.objects.prefetch_related('author__user_favorites__recipes')
        qs = Recipe.objects.filter(user=self.request.user)
        return Recipe.objects.filter(author__follower=self.request.user)


@api_view(http_method_names=['GET', ])
@permission_classes([IsAuthenticated])
def FollowListView(request):
    user = User.objects.filter(following__user=request.user)
    paginator = PageNumberPagination()
    paginator.page_size = 10  #change to PAGE_SIZE
    response = paginator.paginate_queryset(user, request)
    serializer = ListSubscriptionsSerializer(
        response, many=True, context={'current_user': request.user}
    )
    return paginator.get_paginated_response(serializer.data)