from django.contrib import admin
from .models import Cliente, Nota


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'telefone', 'responsavel')
    list_filter = ('responsavel',)


admin.site.register(Nota)
