import json
from django.core.management.base import BaseCommand
from analises.models import Parametro


class Command(BaseCommand):
    help = 'Importa parâmetros de um JSON'

    def handle(self, *args, **kwargs):
        with open('parametros.json', 'r', encoding='utf-8') as f:
            dados = json.load(f)

        objetos = []
        for item in dados:
            objetos.append(
                Parametro(nome=item['nome'])
            )

        Parametro.objects.bulk_create(objetos)

        self.stdout.write(self.style.SUCCESS('Importação concluída com sucesso!'))