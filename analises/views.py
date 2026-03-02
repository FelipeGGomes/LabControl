from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import datetime
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.utils import timezone
from .models import Parametro, Analises, Origem, Analista, AnaliseParametro
import os
from django.conf import settings


def index(request):
    return render(request, 'dashboard.html')

def analises(request):
    if request.method == 'POST':

        # 1️⃣ Captura de IDs (Chaves Estrangeiras)
        origem_id = request.POST.get('origem') or None
        coletador_id = request.POST.get('coletador') or None

        # 2️⃣ Captura de Textos
        proc_bac = request.POST.get('processador_bac')
        proc_dbo = request.POST.get('processador_dbo')
        amostra = request.POST.get('amostra')
        estacao = request.POST.get('estacao')
        lote = request.POST.get('lote')
        controle = request.POST.get('controle')
        obs = request.POST.get('obs')

        # 3️⃣ Captura das Datas e Horas (campos separados no BD)
        dt_coleta = request.POST.get('data_coleta') or None
        hr_coleta = request.POST.get('hora_coleta') or None
        dt_proc_bac = request.POST.get('data_processamento_bac') or None
        hr_proc_bac = request.POST.get('hora_processamento_bac') or None
        dt_inc_dbo = request.POST.get('data_incubacao_dbo') or None
        hr_inc_dbo = request.POST.get('hora_incubacao_dbo') or None

        # 4️⃣ Validação de Duplicidade
        if origem_id and dt_coleta and hr_coleta:
            if Analises.objects.filter(
                origem_id=origem_id,
                data_coleta=dt_coleta,
                hora_coleta=hr_coleta
            ).exists():
                messages.error(
                    request,
                    'Erro: Já existe um registro para esta Origem nesta data/hora.'
                )
                return redirect('analises')

        try:
            # 5️⃣ Salvamento da Análise Principal
            nova_analise = Analises.objects.create(
                origem_id=origem_id,
                amostra=amostra,
                data_coleta=dt_coleta,
                hora_coleta=hr_coleta,
                coletador_id=coletador_id,
                estacao=estacao,
                processador_bac=proc_bac,
                data_processamento_bac=dt_proc_bac,
                hora_processamento_bac=hr_proc_bac,
                processador_dbo=proc_dbo,
                data_incubacao_dbo=dt_inc_dbo,
                hora_incubacao_dbo=hr_inc_dbo,
                lote=lote,
                controle=controle,
                obs=obs
            )

            # 6️⃣ Salvamento Dinâmico dos Parâmetros
            todos_parametros = Parametro.objects.all()

            for p in todos_parametros:

                if request.POST.get(f'param_selecionado_{p.id}'):

                    res = request.POST.get(f'param_resultado_{p.id}')
                    d = request.POST.get(f'param_data_{p.id}')
                    h = request.POST.get(f'param_hora_{p.id}')
                    a_id = request.POST.get(f'param_analista_{p.id}')

                    # Monta datetime do parâmetro
                    if d and h:
                        dt_param = timezone.make_aware(
                            datetime.strptime(f"{d} {h}", "%Y-%m-%d %H:%M")
                        )
                    else:
                        dt_param = None

                    AnaliseParametro.objects.create(
                        analise=nova_analise,
                        parametro=p,
                        resultado=res,
                        data_hora_resultado=dt_param,
                        analista_id=a_id if a_id else None
                    )

            messages.success(request, 'Análise e parâmetros registrados com sucesso!')
            return redirect('analises')

        except Exception as e:
            messages.error(request, f'Erro ao salvar no banco de dados: {e}')
            return redirect('analises')

    # 🔹 Fluxo GET
    contexto = {
        'origens': Origem.objects.all().order_by('nome'),
        'analistas': Analista.objects.all().order_by('nome'),
        'parametros': Parametro.objects.all().order_by('criado_em'),
        'analises_recentes': Analises.objects.all().order_by('-data_coleta')[:10]
    }

    return render(request, 'analises.html', contexto)

def cadastro_parametro(request):
    if request.method == 'POST':
        nome_digitado = request.POST.get('nome')
        
        if nome_digitado: 
            Parametro.objects.create(nome=nome_digitado)
            messages.success(request, f'Parâmetro "{nome_digitado}" salvo com sucesso!')
            return redirect('cadastro_parametro') 
            
    parametros_lista = Parametro.objects.all().order_by('-criado_em')
    
    # Paginação: 5 itens por página
    paginator = Paginator(parametros_lista, 15) 
    page_number = request.GET.get('page')
    parametros_salvos = paginator.get_page(page_number)
    
    return render(request, 'parametros.html', {'parametros': parametros_salvos})

def editar_parametro(request, id):
    parametro = get_object_or_404(Parametro, id=id)
    if request.method == 'POST':
        novo_nome = request.POST.get('nome')
        if novo_nome:
            parametro.nome = novo_nome
            parametro.save()
            messages.success(request, f'Parâmetro "{novo_nome}" atualizado com sucesso!')
            return redirect('cadastro_parametro')
    
 
    parametros_lista = Parametro.objects.all().order_by('-criado_em')
    paginator = Paginator(parametros_lista, 15) 
    page_number = request.GET.get('page')
    parametros_salvos = paginator.get_page(page_number)
    
    return render(request, 'parametros.html', {'parametros': parametros_salvos, 'parametro_em_edicao': parametro})

def excluir_parametro(request, id):
    parametro = get_object_or_404(Parametro, id=id)
    if request.method == 'POST':
        nome = parametro.nome
        parametro.delete()
        messages.success(request, f'Parâmetro "{nome}" excluído com sucesso!')
    return redirect('cadastro_parametro')


def relatorio(request):
    relatorios_lista = Analises.objects.all()

    # Captura dos filtros do GET
    f_origem = request.GET.get('origem')
    f_parametro = request.GET.get('parametro')
    f_data_inicio = request.GET.get('data_inicio')
    f_data_fim = request.GET.get('data_fim')
    f_amostra = request.GET.get('amostra')
    f_coletador = request.GET.get('coletador')

    # Aplicação dos filtros
    if f_origem:
        relatorios_lista = relatorios_lista.filter(origem_id=f_origem)

    if f_coletador:
        relatorios_lista = relatorios_lista.filter(coletador_id=f_coletador)
    
    if f_parametro:
        
        relatorios_lista = relatorios_lista.filter(analiseparametro__parametro_id=f_parametro).distinct()
        
    if f_data_inicio:
        relatorios_lista = relatorios_lista.filter(data_coleta__gte=f_data_inicio)
        
    if f_data_fim:
        relatorios_lista = relatorios_lista.filter(data_coleta__lte=f_data_fim)

    if f_amostra:
        relatorios_lista = relatorios_lista.filter(amostra__icontains=f_amostra)

    relatorios_lista = relatorios_lista.order_by('-data_coleta')

    paginacao = Paginator(relatorios_lista, 15)
    page_number = request.GET.get('page')
    relatorio_page = paginacao.get_page(page_number)

    contexto = {
        'relatorio': relatorio_page,
        'origens': Origem.objects.all().order_by('nome'),
        'parametros': Parametro.objects.all().order_by('nome'),
        'coletadores': Analista.objects.all().order_by('nome'),
    }
    return render(request, 'relatorio.html', contexto)

def ver_relatorio(request, id):
    # Recupera a análise e envia seus parâmetros para a view detalhada
    analise = get_object_or_404(Analises, id=id)
    
    todos_parametros = Parametro.objects.all()
    salvos = AnaliseParametro.objects.filter(analise=analise)
    salvos_dict = {sp.parametro_id: sp for sp in salvos}
    
    parametros_detalhados = []
    for p in todos_parametros:
        parametros_detalhados.append({
            'parametro': p,
            'salvo': salvos_dict.get(p.id)
        })

    contexto = {
        'relatorio': analise,
        'origens': Origem.objects.all().order_by('nome'),
        'coletadores': Analista.objects.all().order_by('nome'),
        'analistas': Analista.objects.all().order_by('nome'),
        'parametros_detalhados': parametros_detalhados,
    }
    return render(request, 'ver_relatorio.html', contexto)

def atualizar_relatorio(request, id):
    analise = get_object_or_404(Analises, id=id)
    
    if request.method == 'POST':
        try:
            # Informações da Amostra
            analise.amostra = request.POST.get('amostra')
            analise.origem_id = request.POST.get('origem')
            
            # Coleta
            analise.data_coleta = request.POST.get('data_coleta') or None
            analise.hora_coleta = request.POST.get('hora_coleta') or None
            
            analise.coletador_id = request.POST.get('coletador') or None
            analise.estacao = request.POST.get('estacao')
            
            # Processamento BAC
            analise.processador_bac = request.POST.get('processador_bac')
            analise.data_processamento_bac = request.POST.get('data_processamento_bac') or None
            analise.hora_processamento_bac = request.POST.get('hora_processamento_bac') or None

            # Processamento DBO
            analise.processador_dbo = request.POST.get('processador_dbo')
            analise.data_incubacao_dbo = request.POST.get('data_incubacao_dbo') or None
            analise.hora_incubacao_dbo = request.POST.get('hora_incubacao_dbo') or None

            # Outros 
            analise.lote = request.POST.get('lote')
            analise.controle = request.POST.get('controle')
            analise.obs = request.POST.get('obs')

            analise.save()

            # Parâmetros Editáveis
            AnaliseParametro.objects.filter(analise=analise).delete()
            todos_parametros = Parametro.objects.all()

            for p in todos_parametros:
                if request.POST.get(f'param_selecionado_{p.id}'):
                    res = request.POST.get(f'param_resultado_{p.id}')
                    d = request.POST.get(f'param_data_{p.id}')
                    h = request.POST.get(f'param_hora_{p.id}')
                    a_id = request.POST.get(f'param_analista_{p.id}')

                    if d and h:
                        dt_param = timezone.make_aware(datetime.strptime(f"{d} {h}", "%Y-%m-%d %H:%M"))
                    else:
                        dt_param = None

                    AnaliseParametro.objects.create(
                        analise=analise,
                        parametro=p,
                        resultado=res,
                        data_hora_resultado=dt_param,
                        analista_id=a_id if a_id else None
                    )

            messages.success(request, f"Relatório da amostra {analise.amostra} atualizado com sucesso!")
            
        except Exception as e:
            messages.error(request, f"Erro ao atualizar: {str(e)}")
            
    return redirect('ver_relatorio', id=analise.id)

def relatorio_pdf(request, id):
    # Pega os mesmos dados da visualização da tela
    analise = get_object_or_404(Analises, id=id)
    
    # Busca os parâmetros específicos dessa análise
    parametros_salvos = AnaliseParametro.objects.filter(analise=analise)
    
    # Monta a lista com os nomes originais dos parâmetros e seus resultados editados
    parametros_detalhados = []
    for sp in parametros_salvos:
        parametros_detalhados.append({
            'nome': sp.parametro.nome,
            'resultado': sp.resultado,
            'unidade': sp.parametro.unidade,
            'metodo': sp.parametro.metodo_referencia,
            'limite': sp.parametro.limite_especificacao,
            'conformidade': sp.parametro.conformidade_padrao
        })

    # Passa o contexto para o template que o usuário desenhou `pdf/relatorio_pdf.html`
    contexto = {
        'relatorio': analise,
        'parametros': parametros_detalhados,
    }

    template = get_template('pdf/relatorio_pdf.html')
    html = template.render(contexto)
    
    # Cria o PDF na memória usando xhtml2pdf
    response = HttpResponse(content_type='application/pdf')
    # Use attachment para forçar download: f'attachment; filename="relatorio_{analise.id}.pdf"'
    # Use inline para abrir no navegador
    response['Content-Disposition'] = f'inline; filename="relatorio_{analise.id}.pdf"'
    
    pisa_status = pisa.CreatePDF(
       html, dest=response
    )
    
    if pisa_status.err:
       return HttpResponse('Ocorreu um erro gerando o PDF <pre>' + html + '</pre>')
    
    return response
            
    return redirect('ver_relatorio', id=analise.id)

def relatorio_pdf(request, id):
    # Pega os mesmos dados da visualização da tela
    analise = get_object_or_404(Analises, id=id)
    
    # Busca os parâmetros específicos dessa análise
    parametros_salvos = AnaliseParametro.objects.filter(analise=analise)
    
    # Monta a lista com os nomes originais dos parâmetros e seus resultados editados
    parametros_detalhados = []
    for sp in parametros_salvos:
        parametros_detalhados.append({
            'nome': sp.parametro.nome,
            'resultado': sp.resultado,
            'unidade': sp.parametro.unidade,
            'metodo': sp.parametro.metodo_referencia,
            'limite': sp.parametro.limite_especificacao,
            'conformidade': sp.parametro.conformidade_padrao
        })

    # Passa o contexto para o template que o usuário desenhou `pdf/relatorio_pdf.html`
    contexto = {
        'relatorio': analise,
        'parametros': parametros_detalhados,
    }

    template = get_template('pdf/relatorio_pdf.html')
    html = template.render(contexto)
    
    # Cria o PDF na memória usando xhtml2pdf
    response = HttpResponse(content_type='application/pdf')
    # Use attachment para forçar download: f'attachment; filename="relatorio_{analise.id}.pdf"'
    # Use inline para abrir no navegador
    response['Content-Disposition'] = f'inline; filename="relatorio_{analise.id}.pdf"'
    
    pisa_status = pisa.CreatePDF(
       html, dest=response
    )
    
    if pisa_status.err:
       return HttpResponse('Ocorreu um erro gerando o PDF <pre>' + html + '</pre>')
    
    return response

def relatorio_pdf(request, id):
    # Pega os mesmos dados da visualização da tela
    analise = get_object_or_404(Analises, id=id)
    
    # Busca os parâmetros específicos dessa análise
    parametros_salvos = AnaliseParametro.objects.filter(analise=analise)
    
    # Monta a lista com os nomes originais dos parâmetros e seus resultados editados
    parametros_detalhados = []
    for sp in parametros_salvos:
        parametros_detalhados.append({
            'nome': sp.parametro.nome,
            'resultado': sp.resultado,
            'unidade': sp.parametro.unidade,
            'metodo': sp.parametro.metodo_referencia,
            'limite': sp.parametro.limite_especificacao,
            'conformidade': sp.parametro.conformidade_padrao
        })

    # Passa o contexto para o template que o usuário desenhou `pdf/relatorio_pdf.html`
    contexto = {
        'relatorio': analise,
        'parametros': parametros_detalhados,
    }

    template = get_template('pdf/relatorio_pdf.html')
    html = template.render(contexto)
    
    # Cria o PDF na memória usando xhtml2pdf
    response = HttpResponse(content_type='application/pdf')
    # Use attachment para forçar download: f'attachment; filename="relatorio_{analise.id}.pdf"'
    # Use inline para abrir no navegador
    response['Content-Disposition'] = f'inline; filename="relatorio_{analise.id}.pdf"'
    
    pisa_status = pisa.CreatePDF(
       html, dest=response
    )
    
    if pisa_status.err:
       return HttpResponse('Ocorreu um erro gerando o PDF <pre>' + html + '</pre>')
    
    return response

def link_callback(uri, rel):
    """
    Converte URLs estáticas para caminhos absolutos do sistema.
    """
    if uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.BASE_DIR, uri.replace(settings.STATIC_URL, "static/"))
    elif uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.BASE_DIR, uri.replace(settings.MEDIA_URL, "media/"))
    else:
        return uri

    if not os.path.isfile(path):
        raise Exception(f'Media URI must start with {settings.STATIC_URL} or {settings.MEDIA_URL}')
    return path

def relatorio_pdf(request, id):
    # 1. Pega os mesmos dados da visualização da tela
    analise = get_object_or_404(Analises, id=id)
    
    # 2. Busca os parâmetros específicos dessa análise
    parametros_salvos = AnaliseParametro.objects.filter(analise=analise)
    
    # 3. Monta a lista com os dados reais disponíveis no banco
    parametros_detalhados = []
    for sp in parametros_salvos:
        parametros_detalhados.append({
            'nome': sp.parametro.nome,
            'resultado': sp.resultado,
            # Como a data_hora_resultado pode ser nula, formatamos de forma segura
            'data_analise': sp.data_hora_resultado.strftime("%d/%m/%Y %H:%M") if sp.data_hora_resultado else "—",
            'analista': sp.analista.nome if sp.analista else "—"
        })

    # 4. Passa o contexto para o template
    contexto = {
        'relatorio': analise,
        'parametros': parametros_detalhados,
    }

    template = get_template('pdf/relatorio_pdf.html')
    html = template.render(contexto)
    
    # 5. Cria o PDF na memória usando xhtml2pdf
    response = HttpResponse(content_type='application/pdf')
    # Use inline para abrir no navegador
    response['Content-Disposition'] = f'inline; filename="relatorio_analise_{analise.id}.pdf"'
    
    # Cria o PDF
    pisa_status = pisa.CreatePDF(
    html,
    dest=response,
    link_callback=link_callback  
)
    
    if pisa_status.err:
        return HttpResponse('Ocorreu um erro gerando o PDF <pre>' + html + '</pre>')
    
    return response