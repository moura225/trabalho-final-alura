from django.urls import path

from .views import (
    ClienteDetailView,
    ClienteListCreateView,
    NotaDetailView,
    NotaListCreateView,
)

urlpatterns = [
    path('', ClienteListCreateView.as_view(), name='cliente-list-create'),
    path(
        '<int:pk>/',
        ClienteDetailView.as_view(),
        name='cliente-detail',
    ),
    path(
        '<int:cliente_id>/notas/',
        NotaListCreateView.as_view(),
        name='cliente-notas-list-create',
    ),
    path(
        '<int:cliente_id>/notas/<int:pk>/',
        NotaDetailView.as_view(),
        name='cliente-nota-detail',
    ),
]
