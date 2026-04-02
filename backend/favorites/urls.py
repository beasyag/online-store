from django.urls import path

from .views import FavoriteListAPIView, FavoriteToggleAPIView

urlpatterns = [
    path("favorites/", FavoriteListAPIView.as_view(), name="favorite-list"),
    path("favorites/toggle/", FavoriteToggleAPIView.as_view(), name="favorite-toggle"),
]

