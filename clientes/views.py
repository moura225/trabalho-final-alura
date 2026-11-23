from django.shortcuts import get_object_or_404
from rest_framework.generics import (
    ListCreateAPIView,
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated

from .models import Cliente, Nota
from .permissions import (
    IsAdministrador,
    IsAdministradorOrOwnClientReadOnly,
    IsAdministradorOrOwnNoteReadOnly,
    IsAdministradorOrVendedor,
    is_administrador,
)
from .serializers import ClienteSerializer, NotaSerializer


class ClienteListCreateView(ListCreateAPIView):
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated, IsAdministradorOrVendedor]

    def get_queryset(self):
        queryset = Cliente.objects.all()
        if not is_administrador(self.request.user):
            queryset = queryset.filter(responsavel=self.request.user)
        for field in ('nome', 'email', 'telefone'):
            value = self.request.query_params.get(field, '').strip()
            if value:
                queryset = queryset.filter(**{f'{field}__icontains': value})
        return queryset

    def perform_create(self, serializer):
        serializer.save(responsavel=self.request.user)


class ClienteDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated, IsAdministradorOrOwnClientReadOnly]

    def get_queryset(self):
        queryset = Cliente.objects.all()
        if not is_administrador(self.request.user):
            queryset = queryset.filter(responsavel=self.request.user)
        return queryset


class NotaListCreateView(ListCreateAPIView):
    serializer_class = NotaSerializer
    permission_classes = [IsAuthenticated, IsAdministradorOrVendedor]

    def get_cliente(self):
        queryset = Cliente.objects.all()
        if not is_administrador(self.request.user):
            queryset = queryset.filter(responsavel=self.request.user)
        return get_object_or_404(queryset, pk=self.kwargs['cliente_id'])

    def get_queryset(self):
        return Nota.objects.filter(cliente=self.get_cliente())

    def perform_create(self, serializer):
        serializer.save(cliente=self.get_cliente())


class NotaDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = NotaSerializer
    permission_classes = [IsAuthenticated, IsAdministradorOrOwnNoteReadOnly]

    def get_cliente(self):
        queryset = Cliente.objects.all()
        if not is_administrador(self.request.user):
            queryset = queryset.filter(responsavel=self.request.user)
        return get_object_or_404(queryset, pk=self.kwargs['cliente_id'])

    def get_queryset(self):
        return Nota.objects.filter(cliente=self.get_cliente())


class NotaAdminListView(ListAPIView):
    queryset = Nota.objects.all()
    serializer_class = NotaSerializer
    permission_classes = [IsAuthenticated, IsAdministrador]
