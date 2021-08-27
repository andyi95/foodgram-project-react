"""Invalidate cache on save-delete signals.

Yet it flushes all the cache on update operations, more accurate logic will be
implemented later :).
"""
from django.core.cache import cache
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from api.models import Ingredient, Recipe, RecipeComponent


@receiver(post_delete, sender=Recipe, dispatch_uid='recipe_deleted')
@receiver(post_save, sender=Recipe, dispatch_uid='recipe_updated')
@receiver(post_save, sender=Ingredient, dispatch_uid='ingredient_updated')
@receiver(post_delete, sender=Ingredient, dispatch_uid='ingredient_updated')
@receiver(m2m_changed, sender=RecipeComponent, dispatch_uid='rc_changed')
def obj_edit_handler(sender, **kwargs):
    """Flush cache on Recipe or its parts change."""
    print("it's done!")
    cache.clear()
