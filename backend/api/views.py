from django_filters.rest_framework import DjangoFilterBackend
from djoser import views
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.filters import RecipeFilter
from api.models import (FavorRecipes, Follow, Ingredient, Recipe,
                        RecipeComponent, ShoppingList, Tag, User)
from api.permissions import IsOwnerOrReadOnly
from api.serializers import (AuthorSerializer, FavorSerializer,
                             FollowSerializer, IngredientSerializer,
                             ListFavorSerializer, NewRecipeSerializer,
                             RecipeSerializer, ShoppingSerializer,
                             TagSerializer)


class GetPostViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                     mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    pass


class GetPostDelViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                        mixins.RetrieveModelMixin, mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    pass


class RecipeViewSet(ModelViewSet):
    permission_classes = [IsOwnerOrReadOnly, ]
    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeSerializer
        else:
            return NewRecipeSerializer


class IngredientsViewSet(GetPostViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['pk', '^name']


class FavoriteViewSet(GetPostDelViewSet):
    permission_classes = [IsAuthenticated]

    def get(self, request, recipe_id):
        user = request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        FavorRecipes.objects.create(author=user, recipes=recipe)
        serializer = FavorSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TagViewSet(GetPostViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class ShoppingViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin,
                      viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ShoppingSerializer

    def perform_create(self, serializer):
        recipe = get_object_or_404(Recipe, pk=self.kwargs.get('recipe_id'))
        serializer.save(author=self.request.user, recipe=recipe)


class AuthorViewSet(views.UserViewSet):
    queryset = User.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]

    @action(methods=['GET', 'DELETE'], detail=True, permission_classes=[IsAuthenticated])
    def follow(self, request, author_id=None):
        user = self.request.user
        following = get_object_or_404(User, id=author_id)
        if request.method == 'GET':
            new_follow = Follow.objects.create(user=user, author=following)
            new_follow.save()
            serializer = FollowSerializer(instance=following, context={'request': request})
            return Response(serializer.data)

    @action(detail=False)
    def subscriptions(self, request):
        print('subscriptions_list')
        user = self.request.user
        follow = Follow.objects.filter(user=user)
        serializer = FollowSerializer(instance=follow, context={'request': request})

