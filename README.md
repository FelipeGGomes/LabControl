# LabControl (CMA - Controle e Monitoramento de Análises)

![Project Status](https://img.shields.io/badge/Status-Em_Desenvolvimento-success)
![Python Version](https://img.shields.io/badge/Python-3.x-blue)
![Django Version](https://img.shields.io/badge/Django-5.x--6.x-green)

O **LabControl** é um sistema web profissional para controle e gestão laboratorial, desenvolvido para gerenciar com eficiência toda a cadeia de análises de amostras (ambiental e controles afins). Com ele, é possível gerir as origens, os profissionais (analistas), parâmetros analisados e emitir relatórios técnicos em formato PDF prontos para impressão ou envio digital.

---

## 🚀 Principais Funcionalidades

- **Gestão de Amostras e Análises:** Lance e rastreie dados completos que incluem Datas, Horários de Coleta e de Processamento de indicativos como Coliformes (BAC) e DBO.
- **Controle de Resultados:** Adicione resultados detalhados por cada parâmetro de análise, garantindo precisão e conformidade.
- **Geração de Relatórios em PDF:** Mecanismo robusto integrado (`xhtml2pdf`) para emitir e exportar os laudos para PDF contendo paginação e timbre institucional.
- **Cadastro Multi-nível:** Gerenciamento organizado de:
  - Origens das Amostras
  - Responsáveis (Analistas/Coletadores)
  - Parâmetros individuais das medições
- **Autenticação e Perfis:** Módulo de controle de usuários (extends `AbstractUser` do Django) assegurando que as informações sigilosas fiquem restritas para quem possui o acesso adequado.

---

## 🛠️ Tecnologias e Ferramentas

O sistema foi construído nas seguintes tecnologias:

- **Back-end:** [Python](https://www.python.org/) & [Django Framework](https://www.djangoproject.com/)
- **Banco de Dados:** SQLite (padrão, mas escalável via ORM para PostgreSQL/MySQL)
- **Front-end:** HTML, Vanilla CSS (com forte estilização customizada focada em UX), Font Awesome.
- **Gerador de PDF:** `xhtml2pdf`

---

## ⚙️ Como executar localmente

Siga o passo a passo abaixo para rodar o LabControl no seu ambiente de desenvolvimento:

### 1. Clonar o repositório

```bash
git clone https://github.com/FelipeGGomes/LabControl.git
cd LabControl
```

### 2. Criar e ativar o Ambiente Virtual (recomendado)

No Windows:
```bash
python -m venv venv
.\venv\Scripts\Activate
```

No Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar o Banco de Dados

Crie as tabelas rodando as migrações originais da aplicação:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Criar o Usuário Administrador (Opcional, recomendado)

```bash
python manage.py createsuperuser
```
*(Você será solicitado a preencher um usuário, email e senha)*

### 6. Iniciar o Servidor de Desenvolvimento

```bash
python manage.py runserver
```

Acesse no seu navegador a URL padrão: `http://127.0.0.1:8000/`

---

## 📂 Estrutura Principal do Projeto

```text
├── analises/             # Aplicação central (Views, Models, Templates, URLs)
│   ├── templates/        # Estrutura visual HTML (páginas web e PDFs)
│   ├── models.py         # Mapeamento e Regras das Tabelas no Banco de Dados
│   └── views.py          # Lógica do back-end para as requisições
├── cma/                  # Diretório principal de configuração global do projeto
│   ├── settings.py       # Configurações do Django (Apps, DB, Variáveis)
│   └── urls.py           # Roteamento global
├── static/               # Arquivos estáticos globais (CSS, Imagens como o logo)
├── requirements.txt      # Arquivo de dependências necessárias do Python
└── manage.py             # Script principal de gerenciamento do Django
```

---

## 📄 Licença

Este projeto é desenvolvido para administração e controle de análises ambientais. A reprodução deve obedecer as restrições e regras corporativas.
