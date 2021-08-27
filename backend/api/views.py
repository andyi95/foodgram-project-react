from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from rest_framework import status, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.filters import IngredientFilter, RecipeFilter
from api.models import (FavorRecipes, Ingredient, Recipe, RecipeComponent,
                        ShoppingList, Tag)
from api.permissions import IsOwnerOrReadOnly
from api.serializers import (FavorSerializer, IngredientSerializer,
                             RecipeReadSerializer, RecipeWriteSerializer,
                             ShoppingSerializer, TagSerializer)
from foodgram_api.settings import CACHE_TIMEOUT


class RecipeViewSet(viewsets.ModelViewSet):
    filter_class = RecipeFilter
    permission_classes = [IsOwnerOrReadOnly]
    queryset = Recipe.objects.prefetch_related(
        'ingredients', 'author', 'tags'
    )

    def get_queryset(self):
        user = self.request.user
        queryset = super(RecipeViewSet, self).get_queryset()
        if user.is_anonymous or user is None:
            return queryset
        return queryset.opt_annotations(user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ['GET', ]:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    @method_decorator(vary_on_cookie)
    @method_decorator(cache_page(CACHE_TIMEOUT))
    def dispatch(self, request, *args, **kwargs):
        return super(RecipeViewSet, self).dispatch(request, *args, **kwargs)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny, )
    filter_class = IngredientFilter
    search_fields = ['name', ]
    pagination_class = None


class CommonViewSet(APIView):
    """Process get and delete methods with a common viewset."""

    permission_classes = [IsOwnerOrReadOnly]
    serializer_class = None
    obj = Recipe
    del_obj = None

    def get(self, request, recipe_id):
        user = request.user
        data = {
            'author': user.id,
            'recipes': recipe_id
        }
        serializer = self.serializer_class(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED)

    def delete(self, request, recipe_id):
        user = request.user
        deletion_obj = get_object_or_404(
            self.del_obj, author=user, recipes_id=recipe_id
        )
        deletion_obj.delete()
        return Response(
            'Removed', status=status.HTTP_204_NO_CONTENT
        )


class FavoriteViewSet(CommonViewSet):
    obj = Recipe
    serializer_class = FavorSerializer
    del_obj = FavorRecipes


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class ShoppingViewSet(CommonViewSet):
    serializer_class = ShoppingSerializer
    obj = Recipe
    del_obj = ShoppingList


class ShoppingCartDL(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Download a shopping list with aggregated sum of ingredients."""
        user = request.user
        shop_list = RecipeComponent.objects.shop_list(user=user)
        wishlist = [f'{item["name"]} - {item["sum"]} '
                    f'{item["unit"]} \r\n' for item in shop_list]
        wishlist.append('\r\n')
        wishlist.append('FoodGram, 2021')
        response = HttpResponse(wishlist, 'Content-Type: text/plain')
        response['Content-Disposition'] = 'attachment; filename="wishlist.txt"'
        return response
