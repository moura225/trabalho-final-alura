from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from .models import Cliente, Nota
from .permissions import ADMINISTRADOR_GROUP, VENDEDOR_GROUP


class ClienteAuthenticationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='usuario',
            password='senha-segura-123',
        )
        self.user.groups.add(Group.objects.get(name=VENDEDOR_GROUP))
        self.client = APIClient()
        self.clientes_url = '/api/clientes/'
        self.token_url = '/api/token/'

    def test_cliente_list_and_create_require_authentication(self):
        list_response = self.client.get(
            self.clientes_url,
            {'nome': 'Ana'},
        )
        create_response = self.client.post(
            self.clientes_url,
            {
                'nome': 'Ana Silva',
                'email': 'ana@example.com',
                'telefone': '11999990000',
            },
            format='json',
        )

        self.assertEqual(list_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(create_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Cliente.objects.count(), 0)

    def test_jwt_login_allows_authenticated_client_access(self):
        token_response = self.client.post(
            self.token_url,
            {'username': 'usuario', 'password': 'senha-segura-123'},
            format='json',
        )

        self.assertEqual(token_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', token_response.data)
        self.assertIn('refresh', token_response.data)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )
        create_response = self.client.post(
            self.clientes_url,
            {
                'nome': 'Ana Silva',
                'email': 'ana@example.com',
                'telefone': '11999990000',
            },
            format='json',
        )
        list_response = self.client.get(self.clientes_url)

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)

    def test_invalid_login_and_jwt_are_rejected(self):
        login_response = self.client.post(
            self.token_url,
            {'username': 'usuario', 'password': 'senha-incorreta'},
            format='json',
        )
        self.client.credentials(HTTP_AUTHORIZATION='Bearer token-invalido')
        protected_response = self.client.get(self.clientes_url)

        self.assertEqual(login_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            protected_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_invalid_customer_data_and_duplicate_email_are_rejected(self):
        self.client.force_authenticate(user=self.user)
        invalid_email_response = self.client.post(
            self.clientes_url,
            {
                'nome': 'Cliente inválido',
                'email': 'email-invalido',
                'telefone': '11999990000',
            },
            format='json',
        )
        valid_response = self.client.post(
            self.clientes_url,
            {
                'nome': 'Ana Silva',
                'email': 'ana@example.com',
                'telefone': '11999990000',
            },
            format='json',
        )
        duplicate_response = self.client.post(
            self.clientes_url,
            {
                'nome': 'Outra Ana',
                'email': 'ana@example.com',
                'telefone': '11888880000',
            },
            format='json',
        )

        self.assertEqual(
            invalid_email_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(valid_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            duplicate_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(Cliente.objects.count(), 1)

    def test_cliente_filters_match_partial_values_without_case_sensitivity(self):
        clientes = [
            Cliente.objects.create(
                nome='Ana Silva',
                email='ana.silva@example.com',
                telefone='11987654321',
                responsavel=self.user,
            ),
            Cliente.objects.create(
                nome='Mariana Souza',
                email='mariana.souza@example.com',
                telefone='21912345678',
                responsavel=self.user,
            ),
            Cliente.objects.create(
                nome='Bruno Costa',
                email='bruno.costa@example.net',
                telefone='11922223333',
                responsavel=self.user,
            ),
        ]
        self.client.force_authenticate(user=self.user)

        name_response = self.client.get(
            self.clientes_url,
            {'nome': 'ANa'},
        )
        email_response = self.client.get(
            self.clientes_url,
            {'email': 'EXAMPLE.NET'},
        )
        phone_response = self.client.get(
            self.clientes_url,
            {'telefone': '98765'},
        )

        self.assertEqual(
            {item['email'] for item in name_response.data},
            {clientes[0].email, clientes[1].email},
        )
        self.assertEqual(
            [item['email'] for item in email_response.data],
            [clientes[2].email],
        )
        self.assertEqual(
            [item['email'] for item in phone_response.data],
            [clientes[0].email],
        )

    def test_cliente_filters_combine_when_multiple_parameters_are_provided(self):
        matching_cliente = Cliente.objects.create(
            nome='Ana Silva',
            email='ana.silva@example.com',
            telefone='11987654321',
            responsavel=self.user,
        )
        Cliente.objects.create(
            nome='Ana Costa',
            email='ana.costa@example.net',
            telefone='11911112222',
            responsavel=self.user,
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            self.clientes_url,
            {
                'nome': 'ana',
                'email': 'EXAMPLE.COM',
                'telefone': '8765',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['email'], matching_cliente.email)

    @override_settings(CORS_ALLOWED_ORIGINS=['http://localhost:3000'])
    def test_cors_allows_only_configured_origin(self):
        allowed_response = self.client.get(
            self.clientes_url,
            HTTP_ORIGIN='http://localhost:3000',
        )
        denied_response = self.client.get(
            self.clientes_url,
            HTTP_ORIGIN='https://untrusted.example',
        )

        self.assertEqual(
            allowed_response.headers.get('access-control-allow-origin'),
            'http://localhost:3000',
        )
        self.assertIsNone(
            denied_response.headers.get('access-control-allow-origin')
        )


class NotaEndpointTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='usuario',
            password='senha-segura-123',
        )
        self.user.groups.add(Group.objects.get(name=VENDEDOR_GROUP))
        self.client = APIClient()
        self.cliente = Cliente.objects.create(
            nome='Ana Silva',
            email='ana@example.com',
            telefone='11999990000',
            responsavel=self.user,
        )
        self.notas_url = f'/api/clientes/{self.cliente.pk}/notas/'

    def test_authenticated_user_can_create_and_list_client_notes_in_order(self):
        self.client.force_authenticate(user=self.user)
        first_response = self.client.post(
            self.notas_url,
            {'texto': 'Primeiro contato'},
            format='json',
        )
        second_response = self.client.post(
            self.notas_url,
            {'texto': 'Retorno agendado'},
            format='json',
        )
        other_cliente = Cliente.objects.create(
            nome='Bruno Costa',
            email='bruno@example.com',
            telefone='11988887777',
            responsavel=self.user,
        )
        Nota.objects.create(cliente=other_cliente, texto='Nota de outro cliente')

        now = timezone.now()
        Nota.objects.filter(pk=first_response.data['id']).update(
            data_criacao=now + timedelta(days=1),
        )
        Nota.objects.filter(pk=second_response.data['id']).update(
            data_criacao=now - timedelta(days=1),
        )
        list_response = self.client.get(self.notas_url)

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertIn('data_criacao', first_response.data)
        self.assertEqual(second_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [nota['texto'] for nota in list_response.data],
            ['Retorno agendado', 'Primeiro contato'],
        )

    def test_note_endpoints_require_authentication(self):
        list_response = self.client.get(self.notas_url)
        create_response = self.client.post(
            self.notas_url,
            {'texto': 'Tentativa sem autenticação'},
            format='json',
        )

        self.assertEqual(list_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(create_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Nota.objects.count(), 0)

    def test_cannot_create_note_for_missing_client(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/clientes/99999/notas/',
            {'texto': 'Nota sem cliente'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Nota.objects.count(), 0)

    def test_note_text_is_required(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.notas_url,
            {},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Nota.objects.count(), 0)


class RoleOwnershipTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.vendedor_a = user_model.objects.create_user(username='vendedor-a')
        self.vendedor_b = user_model.objects.create_user(username='vendedor-b')
        self.administrador = user_model.objects.create_user(
            username='administrador',
        )
        vendedor_group = Group.objects.get(name=VENDEDOR_GROUP)
        admin_group = Group.objects.get(name=ADMINISTRADOR_GROUP)
        self.vendedor_a.groups.add(vendedor_group)
        self.vendedor_b.groups.add(vendedor_group)
        self.administrador.groups.add(admin_group)

        self.cliente_a = Cliente.objects.create(
            nome='Cliente A',
            email='cliente.a@example.com',
            telefone='111',
            responsavel=self.vendedor_a,
        )
        self.cliente_b = Cliente.objects.create(
            nome='Cliente B',
            email='cliente.b@example.com',
            telefone='222',
            responsavel=self.vendedor_b,
        )
        self.nota_a = Nota.objects.create(
            cliente=self.cliente_a,
            texto='Nota do vendedor A',
        )
        self.nota_b = Nota.objects.create(
            cliente=self.cliente_b,
            texto='Nota do vendedor B',
        )
        self.client = APIClient()

    def test_vendedor_is_limited_to_owned_clients_and_notes(self):
        self.client.force_authenticate(user=self.vendedor_a)

        client_list = self.client.get('/api/clientes/')
        own_client = self.client.get(f'/api/clientes/{self.cliente_a.pk}/')
        other_client = self.client.get(f'/api/clientes/{self.cliente_b.pk}/')
        own_notes = self.client.get(
            f'/api/clientes/{self.cliente_a.pk}/notas/',
        )
        other_notes = self.client.get(
            f'/api/clientes/{self.cliente_b.pk}/notas/',
        )
        create_other_note = self.client.post(
            f'/api/clientes/{self.cliente_b.pk}/notas/',
            {'texto': 'Não deve ser criada'},
            format='json',
        )
        edit_own_client = self.client.patch(
            f'/api/clientes/{self.cliente_a.pk}/',
            {'nome': 'Nome alterado'},
            format='json',
        )
        edit_own_note = self.client.patch(
            f'/api/clientes/{self.cliente_a.pk}/notas/{self.nota_a.pk}/',
            {'texto': 'Nota alterada'},
            format='json',
        )

        self.assertEqual(len(client_list.data), 1)
        self.assertEqual(client_list.data[0]['id'], self.cliente_a.pk)
        self.assertEqual(own_client.status_code, status.HTTP_200_OK)
        self.assertEqual(other_client.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(own_notes.status_code, status.HTTP_200_OK)
        self.assertEqual(len(own_notes.data), 1)
        self.assertEqual(other_notes.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(create_other_note.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(edit_own_client.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(edit_own_note.status_code, status.HTTP_403_FORBIDDEN)

    def test_vendedor_created_clients_are_owned_and_roleless_users_are_denied(self):
        self.client.force_authenticate(user=self.vendedor_a)
        create_response = self.client.post(
            '/api/clientes/',
            {
                'nome': 'Novo cliente',
                'email': 'novo@example.com',
                'telefone': '333',
            },
            format='json',
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data['responsavel'], 'vendedor-a')
        self.assertEqual(
            Cliente.objects.get(pk=create_response.data['id']).responsavel,
            self.vendedor_a,
        )

        user_without_role = get_user_model().objects.create_user(
            username='sem-perfil',
        )
        self.client.force_authenticate(user=user_without_role)
        denied_response = self.client.get('/api/clientes/')

        self.assertEqual(denied_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_administrator_can_list_and_edit_any_client_and_note(self):
        self.client.force_authenticate(user=self.administrador)

        client_list = self.client.get('/api/clientes/')
        note_list = self.client.get('/api/notas/')
        edit_client = self.client.patch(
            f'/api/clientes/{self.cliente_b.pk}/',
            {'nome': 'Cliente B atualizado'},
            format='json',
        )
        edit_note = self.client.patch(
            f'/api/clientes/{self.cliente_b.pk}/notas/{self.nota_b.pk}/',
            {'texto': 'Nota atualizada pelo administrador'},
            format='json',
        )

        self.assertEqual(client_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(client_list.data), 2)
        self.assertEqual(note_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(note_list.data), 2)
        self.assertEqual(edit_client.status_code, status.HTTP_200_OK)
        self.assertEqual(edit_note.status_code, status.HTTP_200_OK)
        self.cliente_b.refresh_from_db()
        self.nota_b.refresh_from_db()
        self.assertEqual(self.cliente_b.nome, 'Cliente B atualizado')
        self.assertEqual(
            self.nota_b.texto,
            'Nota atualizada pelo administrador',
        )

    def test_application_server_entries_can_be_imported(self):
        from crm_api.asgi import application as asgi_application
        from crm_api.wsgi import application as wsgi_application

        self.assertTrue(callable(asgi_application))
        self.assertTrue(callable(wsgi_application))
