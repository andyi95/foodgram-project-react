import django_filters as filters

from api.models import Recipe

FILTER_CHOICES = (
    (0, 'True'),
    (1, 'False'),
)


class RecipeFilter(filters.FilterSet):
    """
    Фильтры работают по пред-извлеченным значениям is_favorited и т.д.
    """
    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug'
    )
    is_favorited = filters.BooleanFilter(method='fav_filter')
    is_in_shopping_cart = filters.BooleanFilter(method='shop_filter')

    def fav_filter(self, queryset, name, value):
        return queryset.filter(is_favorited=value)

    def shop_filter(self, queryset, name, value):
        return queryset.filter(is_in_shopping_cart=value)

    class Meta:
        model = Recipe
        fields = ['author', 'tags', ]


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')
