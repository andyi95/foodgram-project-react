from django.urls import include, path
from rest_framework.routers import SimpleRouter

from users.views import FollowReadViewSet, FollowViewSet

v1_user_router = SimpleRouter()
v1_user_router.register(
    'users/subscriptions', viewset=FollowReadViewSet, basename='subscriptions'
)
urlpatterns = [
    path(
        'users/<int:author_id>/subscribe/',
        FollowViewSet.as_view(), name='subscribe'
    ),
    path('', include(v1_user_router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
