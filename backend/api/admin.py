from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import mark_safe

from api.models import FavorRecipes, Ingredient, Recipe, ShoppingList, Tag


class RecipeComponentAdmin(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 0
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeComponentAdmin,)
    list_display = ('name', 'author_link', 'favorite_count', 'tag_list', 'id')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'text', 'ingredients__name')
    list_filter = ('tags', 'author')

    def author_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.author.id])
        return mark_safe('<a href="%s">%s</a>' % (url, obj.author.username))

    def favorite_count(self, obj):
        return obj.favorite_count

    def tag_list(self, obj):
        s = list(obj.tags.values('name'))
        return ', '.join(i['name'] for i in s)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related('tags', 'ingredients')
        queryset = queryset.prefetch_related('favorite_recipes').annotate(
            favorite_count=Count('favorite_recipes')
        )
        return queryset

    # Версия развернута была последняя, но я допустил сразу несколько опечаток
    favorite_count.short_description = 'В избранном'
    tag_list.short_description = 'Тэги'
    author_link.short_description = 'Автор рецепта'


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')


class IngridientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'id')
    search_fields = ('name', )
    list_filter = ('measurement_unit', )


class FavorAdmin(admin.ModelAdmin):
    list_display = ('author', 'recipes', 'id')


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('author', 'recipes', 'id')
    search_fields = (
        'recipes__name', 'recipes__text',
        'author__first_name', 'author__last_name'
    )


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngridientAdmin)
admin.site.register(FavorRecipes, FavorAdmin)
admin.site.register(ShoppingList, ShoppingCartAdmin)
