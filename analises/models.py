from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here..abs

class Usuario(AbstractUser):
    # O Django já gerencia senha, nome de usuário, email, etc.
    cpf = models.CharField(max_length=11, unique=True)
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="usuario_set",
        related_query_name="usuario",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="usuario_set",
        related_query_name="usuario",
    )

    def __str__(self):
        # Você pode retornar o username, o first_name ou o CPF
        return self.username

class Parametro(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome do Parâmetro")
    criado_em = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return self.nome


class Origem(models.Model):        
    nome = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nome


class Analista(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome



class Analises(models.Model):    
    origem = models.ForeignKey('Origem', on_delete=models.CASCADE)
    amostra = models.CharField(max_length=100, blank=True, null=True)
    
    data_coleta = models.DateField(null=True, blank=True)
    hora_coleta = models.TimeField(null=True, blank=True)
    coletador = models.ForeignKey('Analista', on_delete=models.SET_NULL, null=True, related_name='coletas_realizadas')  
    estacao = models.CharField(max_length=100)  
    processador_bac = models.CharField(max_length=100, blank=True, null=True)  
    data_processamento_bac = models.DateField(null=True, blank=True)
    hora_processamento_bac = models.TimeField(null=True, blank=True)
    processador_dbo = models.CharField(max_length=100, blank=True, null=True)  
    data_incubacao_dbo = models.DateField(null=True, blank=True)
    hora_incubacao_dbo = models.TimeField(null=True, blank=True)
    lote = models.CharField(max_length=100)  
    controle = models.CharField(max_length=100)  
    obs = models.TextField(max_length=500, blank=True, null=True)  
    
    def __str__(self):
        return f"Análise {self.id} - {self.origem}"


class AnaliseParametro(models.Model):
    analise = models.ForeignKey(Analises, on_delete=models.CASCADE)
    parametro = models.ForeignKey(Parametro, on_delete=models.CASCADE)
    resultado = models.CharField(max_length=100, null=True, blank=True)
    data_hora_resultado = models.DateTimeField(null=True, blank=True)
    analista = models.ForeignKey(Analista, null=True, blank=True, on_delete=models.SET_NULL)
    
    def __str__(self):
        return f"{self.analise} - {self.parametro}: {self.resultado}"



