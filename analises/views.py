from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import datetime
from django.template.loader import get_template
from django.http import HttpResponse # Para gerar o arquivo
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils import timezone
from datetime import datetime
from django.db.models import Count, Avg, Min, Max, F, Q
from .models import Parametro, Analises, Origem, Analista, AnaliseParametro
import os
from django.conf import settings


def index(request):
    # Contagens gerais para os cards superiores

    analises = Analises.objects.all()
    total_analises = Analises.objects.count()
    total_locais = Origem.objects.count()
    total_parametros = Parametro.objects.count()
    
    # Últimas 5 coletas (Analises) cadastradas
    ultimas_coletas = Analises.objects.select_related('origem').order_by('-data_coleta', '-hora_coleta')[:5]
    
    # Últimos 5 parâmetros preenchidos (atividades recentes no lab)
    ultimos_parametros = AnaliseParametro.objects.select_related('analise', 'parametro', 'analise__origem', 'analista').order_by('-id')[:5]

    contexto = {
        'analises': analises,
        'total_analises': total_analises,
        'total_locais': total_locais,
        'total_parametros': total_parametros,
        'ultimas_coletas': ultimas_coletas,
        'ultimos_parametros': ultimos_parametros,
    }
    return render(request, 'dashboard.html', contexto)

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


def analistas(request):
    if request.method == 'POST':
        nome_analista = request.POST.get('nome')
        if nome_analista:
            Analista.objects.create(nome=nome_analista)
            messages.success(request, f'Analista "{nome_analista}" inserido com sucesso!')
            return redirect('analistas') 
            
    analistas_lista = Analista.objects.all().order_by('nome')
    
    paginator = Paginator(analistas_lista, 15) 
    page_number = request.GET.get('page')
    analistas_salvos = paginator.get_page(page_number)
    
    return render(request, 'analistas.html', {'analistas': analistas_salvos})

def editar_analista(request, id):
    analista = get_object_or_404(Analista, id=id)
    if request.method == 'POST':
        novo_nome = request.POST.get('nome')
        if novo_nome:
            analista.nome = novo_nome
            analista.save()
            messages.success(request, f'Analista "{novo_nome}" atualizado com sucesso!')
            return redirect('analistas')
    
    return render(request, 'analistas_form.html', {'analista': analista})

def excluir_analista(request, id):
    analista = get_object_or_404(Analista, id=id)
    if request.method == 'POST':
        nome = analista.nome
        analista.delete()
        messages.success(request, f'Analista "{nome}" excluído com sucesso!')
    return redirect('analistas')


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

def balancos(request):
    # Contexto Base para popular os Options dos filtros HTML
    origens = Origem.objects.all().order_by('nome')
    parametros = Parametro.objects.all().order_by('nome')
    
    # 1. Recupera valores vindos pelo request GET
    mes_filtro = request.GET.get('mes', '')
    origem_id = request.GET.get('origem', '')
    parametro_id = request.GET.get('parametro', '')
    tipo_filtro = request.GET.get('tipo', '')
    
    # Prepara variaveis para os Card de Totais 
    total_analises = 0
    total_origens = 0
    media_parametro = "0.00"
    mes_referencia = "--"

    # Preparar a Queryset de AnaliseParametro base
    qs = AnaliseParametro.objects.select_related('analise', 'parametro', 'analise__origem')
    
    # 2. Aplicação dinâmica dos Filtros informados na interface Web
    if mes_filtro:
        try:
            # Formato esperado vindido do input month do navegador: "YYYY-MM"
            ano, mes = mes_filtro.split('-')
            # Filtramos que a data_coleta extraída pela chave extrangeira analise tenha esses dados
            qs = qs.filter(analise__data_coleta__year=ano, analise__data_coleta__month=mes)
            mes_referencia = f"{mes}/{ano}"
        except:
            pass

    if origem_id:
        qs = qs.filter(analise__origem_id=origem_id)
        
    if parametro_id:
        qs = qs.filter(parametro_id=parametro_id)

    # 3. Agrupamento (Group by parameter and origen)
    # A view na tela pede pra calcular por Parametro, Origem -> Qtde, Média, Min, Max
    resultados_agrupados = {}
    
    todas_analises = set()
    todas_origens = set()
    soma_params = 0
    qtde_params = 0

    for item in qs:
        # Tenta pegar apenas objetos que tem resultado numérico
        try:
            val = float(str(item.resultado).replace(',', '.'))
        except (ValueError, TypeError):
            continue  # Ignora caso não seja numérico conversível (ex: "Ausente", "< 1")

        # Key de agregação -> (Parametro Nome)
        origem_nome = item.analise.origem.nome if item.analise.origem else "Sem Origem"
        chave = item.parametro.nome
        
        todas_analises.add(item.analise_id)
        if item.analise.origem_id:
            todas_origens.add(item.analise.origem_id)
            
        soma_params += val
        qtde_params += 1
        
        if chave not in resultados_agrupados:
            resultados_agrupados[chave] = {
                'quantidade': 0,
                'soma': 0.0,
                'minimo': val,
                'maximo': val
            }
            
        # Acumula na Chave
        agrupamento = resultados_agrupados[chave]
        agrupamento['quantidade'] += 1
        agrupamento['soma'] += val
        agrupamento['minimo'] = min(agrupamento['minimo'], val)
        agrupamento['maximo'] = max(agrupamento['maximo'], val)

    # 4. Finalização dos dados para a tabela
    balanco_final = []
    for param_nome, dados in resultados_agrupados.items():
        media = dados['soma'] / dados['quantidade'] if dados['quantidade'] > 0 else 0
        balanco_final.append({
            'parametro_nome': param_nome,
            'quantidade': dados['quantidade'],
            'media': media,
            'minimo': dados['minimo'],
            'maximo': dados['maximo'],
            'unidade': '-'  # ou remova essa chave do dicionário
        })

    # Ordenar a listagem final (alfabético no parâmetro)
    balanco_final = sorted(balanco_final, key=lambda x: x['parametro_nome'])

    # 5. Cálculo dos Lotes Específicos (Balneabilidade, Açude, Rio)
    lotes_balneabilidade = [{'lote': k, 'total': 0} for k in ['A', 'B', 'C', 'D', 'E', 'F']]
    lotes_acude = [{'lote': k, 'total': 0} for k in ['K', 'LA', 'LB', 'MA', 'MB', 'N', 'O', 'P', 'QA', 'QB']]
    lotes_rio = [{'lote': k, 'total': 0} for k in ['C', 'D', 'E', 'F', 'G', 'H1', 'SA', 'SB', 'R']]
    
    dict_baln = {d['lote']: d for d in lotes_balneabilidade}
    dict_acude = {d['lote']: d for d in lotes_acude}
    dict_rio = {d['lote']: d for d in lotes_rio}
    
    analises_filtradas = Analises.objects.filter(id__in=todas_analises).select_related('origem')
    for analise in analises_filtradas:
        lote = analise.lote
        if not lote: continue
        origem_nome = analise.origem.nome if analise.origem else ""
        if 'Balneabilidade' in origem_nome and lote in dict_baln:
            dict_baln[lote]['total'] += 1
        elif 'Açude' in origem_nome and lote in dict_acude:
            dict_acude[lote]['total'] += 1
        elif 'Rio' in origem_nome and lote in dict_rio:
            dict_rio[lote]['total'] += 1

    total_analises = len(todas_analises)
    total_origens = len(todas_origens)
    if qtde_params > 0:
        media_parametro = f"{(soma_params / qtde_params):.2f}"

    contexto = {
        'origens': origens,
        'parametros': parametros,
        'balanco': balanco_final,
        'lotes_balneabilidade': lotes_balneabilidade,
        'lotes_acude': lotes_acude,
        'lotes_rio': lotes_rio,
        'total_analises': total_analises,
        'total_origens': total_origens,
        'media_parametro': media_parametro,
        'mes_referencia': mes_referencia
    }
    
    return render(request, 'balanco.html', contexto)

def exportar_balanco(request):
    # 1. Recupera valores vindos pelo request GET (Mesmos filtros)
    mes_filtro = request.GET.get('mes', '')
    origem_id = request.GET.get('origem', '')
    parametro_id = request.GET.get('parametro', '')
    tipo_filtro = request.GET.get('tipo', '')
    
    total_analises = 0
    total_origens = 0
    media_parametro = "0.00"
    mes_referencia = "Todos"
    
    filtro_origem_nome = "Todas"
    filtro_parametro_nome = "Todos"
    filtro_tipo_nome = "Todos"

    qs = AnaliseParametro.objects.select_related('analise', 'parametro', 'analise__origem')
    
    # 2. Aplicação dinâmica dos Filtros informados na interface Web
    if mes_filtro:
        try:
            ano, mes = mes_filtro.split('-')
            qs = qs.filter(analise__data_coleta__year=ano, analise__data_coleta__month=mes)
            mes_referencia = f"{mes}/{ano}"
        except:
            pass

    if origem_id:
        qs = qs.filter(analise__origem_id=origem_id)
        try:
            filtro_origem_nome = Origem.objects.get(id=origem_id).nome
        except:
            pass
            
    if parametro_id:
        qs = qs.filter(parametro_id=parametro_id)
        try:
            filtro_parametro_nome = Parametro.objects.get(id=parametro_id).nome
        except:
            pass
            
    if tipo_filtro:
        filtro_tipo_nome = tipo_filtro.title()

    # 3. Agrupamento
    resultados_agrupados = {}
    todas_analises = set()
    todas_origens = set()
    soma_params = 0
    qtde_params = 0

    for item in qs:
        try:
            val = float(str(item.resultado).replace(',', '.'))
        except (ValueError, TypeError):
            continue 

        origem_nome = item.analise.origem.nome if item.analise.origem else "Sem Origem"
        chave = item.parametro.nome
        
        todas_analises.add(item.analise_id)
        if item.analise.origem_id:
            todas_origens.add(item.analise.origem_id)
            
        soma_params += val
        qtde_params += 1
        
        if chave not in resultados_agrupados:
            resultados_agrupados[chave] = {
                'quantidade': 0,
                'soma': 0.0,
                'minimo': val,
                'maximo': val
            }
            
        agrupamento = resultados_agrupados[chave]
        agrupamento['quantidade'] += 1
        agrupamento['soma'] += val
        agrupamento['minimo'] = min(agrupamento['minimo'], val)
        agrupamento['maximo'] = max(agrupamento['maximo'], val)

    # 4. Finalização dos dados para o relatorio
    balanco_final = []
    for param_nome, dados in resultados_agrupados.items():
        media = dados['soma'] / dados['quantidade'] if dados['quantidade'] > 0 else 0
        balanco_final.append({
            'parametro_nome': param_nome,
            'quantidade': dados['quantidade'],
            'media': media,
            'minimo': dados['minimo'],
            'maximo': dados['maximo'],
            'unidade': '-'
        })

    balanco_final = sorted(balanco_final, key=lambda x: x['parametro_nome'])

    # 5. Cálculo dos Lotes Específicos (Balneabilidade, Açude, Rio)
    lotes_balneabilidade = [{'lote': k, 'total': 0} for k in ['A', 'B', 'C', 'D', 'E', 'F']]
    lotes_acude = [{'lote': k, 'total': 0} for k in ['K', 'LA', 'LB', 'MA', 'MB', 'N', 'O', 'P', 'QA', 'QB']]
    lotes_rio = [{'lote': k, 'total': 0} for k in ['C', 'D', 'E', 'F', 'G', 'H1', 'SA', 'SB', 'R']]
    
    dict_baln = {d['lote']: d for d in lotes_balneabilidade}
    dict_acude = {d['lote']: d for d in lotes_acude}
    dict_rio = {d['lote']: d for d in lotes_rio}
    
    analises_filtradas = Analises.objects.filter(id__in=todas_analises).select_related('origem')
    for analise in analises_filtradas:
        lote = analise.lote
        if not lote: continue
        origem_nome = analise.origem.nome if analise.origem else ""
        if 'Balneabilidade' in origem_nome and lote in dict_baln:
            dict_baln[lote]['total'] += 1
        elif 'Açude' in origem_nome and lote in dict_acude:
            dict_acude[lote]['total'] += 1
        elif 'Rio' in origem_nome and lote in dict_rio:
            dict_rio[lote]['total'] += 1

    total_analises = len(todas_analises)
    total_origens = len(todas_origens)
    if qtde_params > 0:
        media_parametro = f"{(soma_params / qtde_params):.2f}"

    contexto = {
        'balanco': balanco_final,
        'lotes_balneabilidade': lotes_balneabilidade,
        'lotes_acude': lotes_acude,
        'lotes_rio': lotes_rio,
        'total_analises': total_analises,
        'total_origens': total_origens,
        'media_parametro': media_parametro,
        'mes_referencia': mes_referencia,
        'filtro_origem': filtro_origem_nome,
        'filtro_parametro': filtro_parametro_nome,
        'filtro_tipo': filtro_tipo_nome,
    }

    template = get_template('pdf/balanco_pdf.html')
    html = template.render(contexto)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="balanco_mensal.pdf"'
    
    pisa_status = pisa.CreatePDF(
        html,
        dest=response,
        link_callback=link_callback  
    )
    
    if pisa_status.err:
        return HttpResponse('Ocorreu um erro gerando o PDF <pre>' + html + '</pre>')
    
    return response