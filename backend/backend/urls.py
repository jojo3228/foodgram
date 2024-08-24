from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from api.views import redirect_link

urlpatterns = [
    path('s/<str:recipe_hash>/', redirect_link, name='redirect-link'),
    # path('s/5Pfng5/', redirect_link, name='redirect-link'),

    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
