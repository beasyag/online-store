from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/", include("products.urls")),
    path("api/", include("sellers.urls")),
    path("api/", include("cart.urls")),
    path("api/", include("orders.urls")),
    path("api/", include("reviews.urls")),
    path("api/", include("favorites.urls")),
    path("api/", include("recommendations.urls")),
]

