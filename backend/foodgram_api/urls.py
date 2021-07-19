from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.flatpages import views
from django.urls import include, path
from foodgram_api import settings

# import debug_toolbar

urlpatterns = [
    # path('__debug__/', include(debug_toolbar.urls)),
    path('jet/', include('jet.urls', 'jet')),
    path('admin/', admin.site.urls),
    # path('auth/', include('django.contrib.auth.urls')),
    path('api/', include('api.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
