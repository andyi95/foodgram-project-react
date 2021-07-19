import django_filters as filters

from api.models import Recipe, FavorRecipes, Tag

class RecipeFilter(filters.FilterSet):
    # is_favorited = filters.BooleanFilter(field_name=)

    class Meta:
        model = Recipe
        fields = ['author', 'tags']