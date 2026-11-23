from rest_framework import serializers

from .models import Cliente, Nota


class ClienteSerializer(serializers.ModelSerializer):
    responsavel = serializers.CharField(
        source='responsavel.username',
        read_only=True,
    )

    class Meta:
        model = Cliente
        fields = ['id', 'nome', 'email', 'telefone', 'responsavel']


class NotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nota
        fields = ['id', 'texto', 'data_criacao']
        read_only_fields = ['id', 'data_criacao']
