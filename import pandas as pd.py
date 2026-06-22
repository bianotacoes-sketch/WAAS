import pandas as pd
from sentence_transformers import SentenceTransformer, util
import ollama
import numpy as np
from datetime import datetime
import re
import json

# ============================================
# CONFIGURAÇÕES
# ============================================
TELEFONE_CONTATO = "(31) 98640-9761"
MODELO_OLLAMA = "llama3.1:8b"  # Modelo avançado para respostas

# Horário de funcionamento
HORARIO_INICIO = "08:00"
HORARIO_FIM = "00:00"
DIAS_SEMANA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado"]
DIA_FECHADO = "domingo"

# ============================================
# 1. BASE DE CONHECIMENTO COMPLETA
# ============================================
servicos_completos = {
    'corte de cabelo masculino': {
        'valor': 40,
        'categoria': 'masculino',
        'tempo_duracao': '30 min',
        'descricao': 'Corte tradicional com tesoura e máquina',
        'sinonimos': ['corte masculino', 'cabelo masculino', 'corte homem', 'cabelo homem', 'corte social']
    },
    'corte de barba': {
        'valor': 45,
        'categoria': 'barba',
        'tempo_duracao': '20 min',
        'descricao': 'Barba completa com navalha e toalha quente',
        'sinonimos': ['barba', 'fazer barba', 'aparar barba', 'barba completa']
    },
    'corte de cabelo feminino': {
        'valor': 50,
        'categoria': 'feminino',
        'tempo_duracao': '45 min',
        'descricao': 'Corte personalizado para cabelo feminino',
        'sinonimos': ['corte feminino', 'cabelo feminino', 'corte mulher']
    },
    'escova': {
        'valor': 35,
        'categoria': 'feminino',
        'tempo_duracao': '40 min',
        'descricao': 'Escova modeladora com secagem',
        'sinonimos': ['escova', 'escova progressiva', 'alisamento']
    },
    'manicure': {
        'valor': 30,
        'categoria': 'manicure',
        'tempo_duracao': '30 min',
        'descricao': 'Cuidados com as unhas das mãos',
        'sinonimos': ['manicure', 'unha da mão', 'fazer unha']
    },
    'pedicure': {
        'valor': 35,
        'categoria': 'pedicure',
        'tempo_duracao': '35 min',
        'descricao': 'Cuidados com as unhas dos pés',
        'sinonimos': ['pedicure', 'unha do pé']
    },
    'hidratação capilar': {
        'valor': 60,
        'categoria': 'tratamento',
        'tempo_duracao': '50 min',
        'descricao': 'Hidratação profunda com produtos especiais',
        'sinonimos': ['hidratação', 'hidratar', 'tratamento capilar']
    },
    'progressiva': {
        'valor': 120,
        'categoria': 'tratamento',
        'tempo_duracao': '2 horas',
        'descricao': 'Alisamento definitivo com escova progressiva',
        'sinonimos': ['progressiva', 'escova progressiva', 'definitiva']
    },
    'sobrancelha': {
        'valor': 25,
        'categoria': 'sobrancelha',
        'tempo_duracao': '20 min',
        'descricao': 'Design e modelagem de sobrancelhas',
        'sinonimos': ['sobrancelha', 'design sobrancelha', 'henna']
    }
}

# Promoções
promocoes = {
    'pacote_beleza': {
        'nome': 'Pacote Beleza Total',
        'descricao': 'corte de cabelo feminino + hidratação capilar',
        'preco_normal': 110,
        'preco_promocional': 100,
        'validade': '2025-12-31'
    },
    'combo_masculino': {
        'nome': 'Combo Executivo',
        'descricao': 'corte de cabelo masculino + barba',
        'preco_normal': 85,
        'preco_promocional': 75,
        'validade': '2025-12-31'
    }
}

# ============================================
# 2. INICIALIZAR SBERT PARA EXTRAÇÃO DE ENTIDADES
# ============================================
print("🚀 Carregando SBERT para extração inteligente...")
modelo_sbert = SentenceTransformer('all-MiniLM-L6-v2')

# Criar embeddings para todos os serviços e sinônimos
todos_termos = []
mapeamento_termo_servico = {}

for servico, dados in servicos_completos.items():
    # Adiciona serviço principal
    todos_termos.append(servico)
    mapeamento_termo_servico[servico] = servico
    
    # Adiciona sinônimos
    for sinonimo in dados['sinonimos']:
        todos_termos.append(sinonimo)
        mapeamento_termo_servico[sinonimo] = servico

# Embeddings para identificação de serviços
embeddings_termos = modelo_sbert.encode(todos_termos, convert_to_tensor=True)

print(f"✅ SBERT pronto! {len(servicos_completos)} serviços carregados.\n")

# ============================================
# 3. FUNÇÕES DE EXTRAÇÃO COM SBERT
# ============================================
def extrair_intencao_e_entidades(pergunta):
    """
    Usa SBERT para extrair informações estruturadas da pergunta
    Retorna: dict com serviço, valor, intenção, etc.
    """
    pergunta_lower = pergunta.lower()
    
    # 1. Identificar o serviço mais relevante
    embedding_pergunta = modelo_sbert.encode(pergunta_lower, convert_to_tensor=True)
    similaridades = util.cos_sim(embedding_pergunta, embeddings_termos)[0]
    melhor_indice = np.argmax(similaridades.cpu().numpy())
    melhor_termo = todos_termos[melhor_indice]
    score_confianca = similaridades[melhor_indice].item()
    
    servico_principal = mapeamento_termo_servico.get(melhor_termo, melhor_termo)
    dados_servico = servicos_completos.get(servico_principal, {})
    
    # 2. Identificar intenção do usuário
    intencao = "informacao_generica"
    
    # Palavras-chave para diferentes intenções
    if any(word in pergunta_lower for word in ['preço', 'valor', 'custa', 'quanto', 'preço']):
        intencao = "consultar_preco"
    elif any(word in pergunta_lower for word in ['horário', 'funciona', 'abre', 'fecha', 'atende']):
        intencao = "consultar_horario"
    elif any(word in pergunta_lower for word in ['promoção', 'desconto', 'oferta', 'pacote']):
        intencao = "consultar_promocao"
    elif any(word in pergunta_lower for word in ['agendar', 'marcar', 'reservar', 'horario disponivel']):
        intencao = "agendar_servico"
    elif any(word in pergunta_lower for word in ['demora', 'tempo', 'duração', 'quanto tempo']):
        intencao = "consultar_tempo"
    elif any(word in pergunta_lower for word in ['local', 'endereço', 'onde fica', 'como chegar']):
        intencao = "consultar_localizacao"
    
    # 3. Verificar se menciona promoção específica
    promocao_mencionada = None
    for promo_key, promo_data in promocoes.items():
        if any(termo in pergunta_lower for termo in promo_data['descricao'].split()):
            promocao_mencionada = promo_key
            break
    
    # 4. Extrair possíveis combinações de serviços
    servicos_mencionados = [servico_principal]
    for servico in servicos_completos.keys():
        if servico != servico_principal and servico in pergunta_lower:
            servicos_mencionados.append(servico)
    
    return {
        'servico_principal': servico_principal,
        'dados_servico': dados_servico,
        'confianca': score_confianca,
        'intencao': intencao,
        'promocao_mencionada': promocao_mencionada,
        'servicos_mencionados': servicos_mencionados,
        'pergunta_original': pergunta
    }

def obter_contexto_completo(entidades):
    """Gera contexto estruturado para o Ollama baseado nas entidades extraídas"""
    
    contexto = {
        'servico': entidades['servico_principal'],
        'valor': entidades['dados_servico'].get('valor', 'Não informado'),
        'categoria': entidades['dados_servico'].get('categoria', 'Geral'),
        'tempo_estimado': entidades['dados_servico'].get('tempo_duracao', 'Não informado'),
        'descricao': entidades['dados_servico'].get('descricao', ''),
        'intencao_cliente': entidades['intencao'],
        'confianca_identificacao': f"{entidades['confianca']:.1%}"
    }
    
    # Adicionar horário atual
    agora = datetime.now()
    contexto['horario_atual'] = agora.strftime('%H:%M')
    contexto['dia_semana'] = agora.strftime('%A')
    
    # Adicionar informações de promoção se relevante
    if entidades['promocao_mencionada']:
        promo = promocoes[entidades['promocao_mencionada']]
        contexto['promocao'] = {
            'nome': promo['nome'],
            'descricao': promo['descricao'],
            'preco_normal': promo['preco_normal'],
            'preco_promocional': promo['preco_promocional']
        }
    
    # Adicionar combos relevantes
    if len(entidades['servicos_mencionados']) > 1:
        contexto['combo_detectado'] = entidades['servicos_mencionados']
        
        # Verificar se existe combo especial
        if 'corte de cabelo masculino' in entidades['servicos_mencionados'] and 'corte de barba' in entidades['servicos_mencionados']:
            contexto['combo_sugerido'] = promocoes['combo_masculino']
        elif 'corte de cabelo feminino' in entidades['servicos_mencionados'] and 'hidratação capilar' in entidades['servicos_mencionados']:
            contexto['combo_sugerido'] = promocoes['pacote_beleza']
    
    return contexto

# ============================================
# 4. FUNÇÃO DE RESPOSTA COM OLLAMA (RESPONSÁVEL POR TUDO)
# ============================================
def resposta_ollama_com_sbert(pergunta):
    """
    Ollama gera a resposta completa usando as informações extraídas pelo SBERT
    """
    
    # Passo 1: SBERT extrai informações estruturadas
    entidades = extrair_intencao_e_entidades(pergunta)
    contexto = obter_contexto_completo(entidades)
    
    # Passo 2: Verificar horário de funcionamento
    horario_valido, msg_horario = verificar_horario_funcionamento()
    contexto['horario_valido'] = horario_valido
    contexto['mensagem_horario'] = msg_horario
    
    # Passo 3: Construir prompt rico para o Ollama
    prompt = f"""Você é a assistente virtual do salão/barbearia "Estilo & Cia". Use as informações abaixo para responder o cliente de forma NATURAL, CALOROSA e PESSOAL.

## INFORMAÇÕES EXTRAÍDAS DA PERGUNTA (pelo sistema SBERT):
- Pergunta do cliente: "{pergunta}"
- Intenção identificada: {contexto['intencao_cliente']}
- Serviço principal: {contexto['servico']}
- Preço: R$ {contexto['valor']},00
- Categoria: {contexto['categoria']}
- Tempo estimado: {contexto['tempo_estimado']}
- Descrição: {contexto['descricao']}
- Confiança na identificação: {contexto['confianca_identificacao']}

## HORÁRIO:
- Agora são: {contexto['horario_atual']}
- {contexto['mensagem_horario']}

## REGRAS IMPORTANTES:
1. **SEMPRE** seja simpático(a) e use emojis quando apropriado
2. Responda de acordo com a INTENÇÃO do cliente:
   - Se for "consultar_preco": Confirme o serviço e informe o valor
   - Se for "consultar_horario": Informe os horários completos
   - Se for "consultar_promocao": Destaque as promoções com entusiasmo
   - Se for "agendar_servico": Informe que é necessário ligar (forneça o telefone)
   - Se for "consultar_tempo": Informe a duração estimada
3. Se houver promoção ou combo relevante, mencione com entusiasmo
4. Se o horário estiver fora do expediente, sugira agendamento
5. Seja breve e objetivo (máximo 4-5 frases)

## SEU TELEFONE PARA CONTATO:
📞 {TELEFONE_CONTATO}

AGORA, RESPONDA O CLIENTE DE FORMA NATURAL E ÚTIL:
"""

    # Adicionar informações de promoção se disponíveis
    if 'promocao' in contexto:
        prompt += f"""
🎉 **PROMOÇÃO DETECTADA:**
- {contexto['promocao']['nome']}: {contexto['promocao']['descricao']}
- De R$ {contexto['promocao']['preco_normal']},00 por APENAS R$ {contexto['promocao']['preco_promocional']},00!
"""

    if 'combo_sugerido' in contexto:
        combo = contexto['combo_sugerido']
        prompt += f"""
💎 **COMBO SUGERIDO:**
- {combo['nome']}: {combo['descricao']}
- Preço especial: R$ {combo['preco_promocional']},00 (economize R$ {combo['preco_normal'] - combo['preco_promocional']},00!)
"""

    # Passo 4: Ollama gera a resposta completa
    try:
        resposta = ollama.chat(
            model=MODELO_OLLAMA,
            messages=[
                {'role': 'system', 'content': 'Você é uma assistente simpática, profissional e prestativa de um salão de beleza/barbearia. Suas respostas são calorosas, informativas e sempre incluem informações relevantes como preços e horários. Use emojis para tornar a conversa mais amigável, mas sem exageros.'},
                {'role': 'user', 'content': prompt}
            ],
            options={
                'temperature': 0.7,
                'top_p': 0.9
            }
        )
        
        resposta_final = resposta['message']['content']
        
        # Adiciona diagnóstico em modo debug (opcional)
        debug_info = f"\n\n🔍 [DEBUG - Confiança SBERT: {contexto['confianca_identificacao']} | Intenção: {contexto['intencao_cliente']}]"
        
        return resposta_final, debug_info, contexto
        
    except Exception as e:
        print(f"⚠️ Erro no Ollama: {e}")
        return fallback_sem_ollama(entidades, contexto), "", contexto

def fallback_sem_ollama(entidades, contexto):
    """Resposta de emergência se o Ollama falhar"""
    return f"""💇‍♀️ Olá! Sobre {entidades['servico_principal']}:

💰 Preço: R$ {contexto['valor']},00
⏱️ Duração: {contexto['tempo_estimado']}
📞 Para agendar: {TELEFONE_CONTATO}

{contexto['mensagem_horario']}

Posso ajudar com mais alguma informação? 😊"""

# ============================================
# 5. FUNÇÕES AUXILIARES
# ============================================
def verificar_horario_funcionamento():
    agora = datetime.now()
    dia_semana = agora.strftime('%A').lower()
    
    dias_traduzidos = {
        'monday': 'segunda', 'tuesday': 'terça', 'wednesday': 'quarta',
        'thursday': 'quinta', 'friday': 'sexta', 'saturday': 'sábado',
        'sunday': 'domingo'
    }
    
    dia_atual = dias_traduzidos.get(dia_semana, dia_semana)
    
    if dia_atual == DIA_FECHADO:
        return False, f"Estamos fechados aos {DIA_FECHADO}s. Funcionamos de {DIAS_SEMANA[0]} a {DIAS_SEMANA[-1]} das {HORARIO_INICIO} às {HORARIO_FIM}"
    
    hora_atual = agora.strftime('%H:%M')
    if hora_atual < HORARIO_INICIO or hora_atual > HORARIO_FIM:
        return False, f"Estamos fechados agora. Nosso horário é {DIAS_SEMANA[0]} a {DIAS_SEMANA[-1]} das {HORARIO_INICIO} às {HORARIO_FIM}"
    
    return True, f"Estamos abertos! Funcionamos de {DIAS_SEMANA[0]} a {DIAS_SEMANA[-1]} das {HORARIO_INICIO} às {HORARIO_FIM}"

def obter_mensagem_horario():
    return f"🕐 {DIAS_SEMANA[0].capitalize()} a {DIAS_SEMANA[-1].capitalize()}: {HORARIO_INICIO} às {HORARIO_FIM} | {DIA_FECHADO.capitalize()}: FECHADO"

# ============================================
# 6. CHAT PRINCIPAL
# ============================================
def chat():
    print("="*65)
    print("💇‍♂️ ASSISTENTE INTELIGENTE - ESTILO & CIA 💅")
    print("="*65)
    print(f"🤖 Como funciona: SBERT extrai informações → Ollama gera resposta natural")
    print(f"🎯 Vantagens:")
    print(f"   • Respostas mais naturais e personalizadas")
    print(f"   • Entende contexto e intenção")
    print(f"   • Sugere promoções relevantes")
    print(f"   • Tratamento diferenciado para cada tipo de pergunta")
    print("-"*65)
    print(f"📞 Contato: {TELEFONE_CONTATO}")
    print(f"🕐 Horário: {obter_mensagem_horario()}")
    print("-"*65)
    print("Digite 'sair' para encerrar")
    print("Digite 'debug' para mostrar diagnóstico detalhado")
    print("-"*65)
    
    mostrar_debug = False
    
    while True:
        pergunta = input("\n🗣️ Você: ").strip()
        
        if pergunta.lower() in ['sair', 'exit', 'quit', 'fim']:
            print("\n✨ Obrigado! Agende seu horário e volte sempre! ✨")
            break
        
        if pergunta.lower() == 'debug':
            mostrar_debug = not mostrar_debug
            print(f"\n🔍 Modo debug: {'ATIVADO' if mostrar_debug else 'DESATIVADO'}")
            continue
        
        if not pergunta:
            print("⚠️ Por favor, digite uma pergunta.")
            continue
        
        print("\n🤔 Processando sua pergunta...")
        
        # Gera resposta usando SBERT + Ollama
        resposta, debug_info, contexto = resposta_ollama_com_sbert(pergunta)
        
        print(f"\n💇‍♀️ Assistente: {resposta}")
        
        if mostrar_debug:
            print(debug_info)
            print(f"\n📊 [DIAGNÓSTICO]")
            print(f"   Serviço: {contexto['servico']}")
            print(f"   Intenção: {contexto['intencao_cliente']}")
            print(f"   Confiança: {contexto['confianca_identificacao']}")
            if 'promocao' in contexto:
                print(f"   🎉 Promoção detectada!")
            if 'combo_sugerido' in contexto:
                print(f"   💎 Combo sugerido!")
        
        print("-"*65)

# ============================================
# 7. TESTE COMPARATIVO
# ============================================
def testar_sistema():
    """Testa o sistema com várias perguntas para mostrar a diferença"""
    print("\n🧪 TESTE COMPARATIVO 🧪")
    print("="*65)
    
    perguntas_teste = [
        "Qual o valor do corte masculino?",
        "preco da barba",
        "quanto custa manicure e pedicure?",
        "vocês abrem domingo?",
        "tem promoção de cabelo feminino?",
        "quanto tempo demora uma progressiva?",
        "corte feminino com hidratação sai mais barato?",
        "como faço para agendar?"
    ]
    
    for pergunta in perguntas_teste:
        print(f"\n📝 Pergunta: {pergunta}")
        print("-" * 40)
        
        # Extrai informações com SBERT
        entidades = extrair_intencao_e_entidades(pergunta)
        
        print(f"🔍 SBERT identificou:")
        print(f"   • Serviço: {entidades['servico_principal']}")
        print(f"   • Confiança: {entidades['confianca']:.1%}")
        print(f"   • Intenção: {entidades['intencao']}")
        
        if entidades['promocao_mencionada']:
            print(f"   • Promoção detectada!")
        
        if len(entidades['servicos_mencionados']) > 1:
            print(f"   • Múltiplos serviços: {entidades['servicos_mencionados']}")
        
        print(f"\n💬 Resposta do assistente:")
        resposta, _, _ = resposta_ollama_com_sbert(pergunta)
        print(f"   {resposta}")
        print("-" * 65)
    
    print("\n✨ Teste concluído!")

# ============================================
# 8. EXECUÇÃO PRINCIPAL
# ============================================
if __name__ == "__main__":
    try:
        print("🔌 Verificando conexão com Ollama...")
        ollama.list()
        print("✅ Ollama conectado com sucesso!")
        
        # Verifica modelo
        modelos = ollama.list()
        modelo_existe = False
        if 'models' in modelos:
            for m in modelos['models']:
                if MODELO_OLLAMA in str(m.get('name', '')):
                    modelo_existe = True
                    break
        
        if not modelo_existe:
            print(f"📥 Baixando modelo {MODELO_OLLAMA}...")
            ollama.pull(MODELO_OLLAMA)
            print("✅ Modelo pronto!")
        
        # Menu principal
        print("\n" + "="*65)
        opcao = input("Escolha uma opção:\n1 - Testar sistema\n2 - Iniciar chat\n\nOpção: ").strip()
        
        if opcao == '1':
            testar_sistema()
        else:
            chat()
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("\nCertifique-se que o Ollama está rodando: ollama serve")
        print("Ou instale: pip install ollama sentence-transformers pandas numpy")