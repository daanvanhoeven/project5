from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # DIT IS DE BELANGRIJKSTE REGEL
    path('', include('app.urls')),
]
