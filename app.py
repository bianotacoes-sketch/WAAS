from flask import Flask, render_template, request, jsonify, session,redirect, url_for, render_template_string
from flask_session import Session
from db_config import init_database, get_db_connection
from admin_routes import admin_bp, merge_layout_config
import json
from datetime import datetime, timedelta
import os
import io
from flask import send_file

SUSPENSION_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Site Indisponível</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #f59e0b;
        }
        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            padding: 20px;
            box-sizing: border-box;
        }
        .container {
            max-width: 500px;
            text-align: center;
            background: var(--card-bg);
            padding: 40px;
            border-radius: 24px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .icon {
            font-size: 64px;
            color: var(--primary);
            margin-bottom: 24px;
            animation: pulse 2s infinite ease-in-out;
        }
        h1 {
            font-size: 28px;
            font-weight: 800;
            margin: 0 0 16px 0;
        }
        p {
            color: var(--text-muted);
            font-size: 16px;
            line-height: 1.6;
            margin: 0 0 24px 0;
        }
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: var(--primary);
            color: #000;
            padding: 12px 24px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.05); opacity: 0.8; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
        <h1>Site Temporariamente Indisponível</h1>
        <p>Este site está temporariamente indisponível. Se você é o proprietário, por favor entre em contato com o suporte para regularizar a sua situação.</p>
        {% if whatsapp %}
        <a href="https://wa.me/{{ whatsapp }}" class="btn" target="_blank">
            <i class="fa-brands fa-whatsapp"></i> Falar com o Suporte
        </a>
        {% endif %}
    </div>
</body>
</html>
"""


def obter_usuario_id_atual():
    cliente_atual = session.get('cliente_atual')
    if not cliente_atual:
        empresa_id, site_id = 1, 1
    else:
        empresa_id = cliente_atual.get('empresa_id', 1)
        site_id = cliente_atual.get('site_id', 1)
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ID FROM TESTE.USUARIOS WHERE EMPRESA_ID = ? AND SITE_ID = ? ORDER BY ID", (empresa_id, site_id))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
        return 3
    except Exception as e:
        print(f"Erro ao obter_usuario_id_atual: {e}")
        return 3

app = Flask(__name__)

# Configurações de segurança
app.secret_key = 'sua_chave_secreta_aqui_mude_para_producao'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False

Session(app)

# Inicializar banco de dados
print("Inicializando banco de dados...")
init_database()
print("Banco de dados pronto!")

# Registrar blueprints
app.register_blueprint(admin_bp)

@app.route('/')
def home():
    """Página inicial do cliente"""
    try:
        from models import AdminModel
        cliente = AdminModel.buscar_dados_cliente(1)
        if cliente:
            layout_config = merge_layout_config(cliente.get('layout_config'))
                      # Buscar aparencia_config para o cliente padrão
            aparencia_config = {}
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT PERSONALIZAR_APARENCIA FROM TESTE.USUARIOS WHERE CLIENTE_ID = 1")
                row = cursor.fetchone()
                conn.close()
                if row and row[0]:
                    aparencia_config = json.loads(row[0])
            except Exception as db_err:
                print(f"Erro ao buscar aparencia_config: {db_err}")
                
            from models import AdminModel
            if AdminModel.verificar_existe_logo(1, 1):
                logo_url = "/img/logo/1/1"
            else:
                logo_url = cliente['logo_url']

            # Salvar na sessão qual cliente está sendo acessado
            session['cliente_atual'] = {
                'id': cliente['id'],
                'nome': cliente['nome_fantasia'],
                'cor_primaria': cliente['cor_primaria'] if cliente['cor_primaria'] else '#667eea',
                'cor_secundaria': cliente['cor_secundaria'] if cliente['cor_secundaria'] else '#764ba2',
                'cor_terciaria': cliente['cor_terciaria'] if cliente['cor_terciaria'] else '#48bb78',
                'logo_url': logo_url,
                'whatsapp': cliente['whatsapp'],
                'url_amigavel': cliente['url_amigavel'],
                'empresa_id': 1,
                'site_id': 1,
                'layout_config': layout_config
            }

            return render_template('cliente_home.html', 
                                   cliente_nome=cliente['nome_fantasia'],
                                   cor_primaria=cliente['cor_primaria'],
                                   cor_secundaria=cliente['cor_secundaria'],
                                   whatsapp=cliente['whatsapp'],
                                   logo_url=logo_url,
                                   layout_config=layout_config,
                                   titulo_site=aparencia_config.get('titulo_site', ''),
                                   corpo_site=aparencia_config.get('corpo_site', ''),
                                   aparencia_config=aparencia_config)
    except Exception as e:
        print(f"Erro ao carregar home padrão: {e}")
    return render_template('cliente_home.html', layout_config={}, aparencia_config={})

@app.route('/agendamento')
def agendamento():
    """Página de agendamento"""
    try:
        from models import AdminModel
        cliente = AdminModel.buscar_dados_cliente(1)
        if cliente:
            layout_config = merge_layout_config(cliente.get('layout_config'))
            cliente['layout_config'] = layout_config
            return render_template('agendamento.html', cliente=cliente)
    except Exception as e:
        print(f"Erro ao carregar agendamento padrão: {e}")
    return render_template('agendamento.html', cliente={})

@app.route('/api/servicos_cliente')
def api_servicos_cliente():
    """Retorna lista de serviços disponíveis"""
    try:
        from models import AdminModel
        cliente_atual = session.get('cliente_atual')
        if cliente_atual:
            empresa_id = cliente_atual.get('empresa_id', 1)
            site_id = cliente_atual.get('site_id', 1)
        else:
            empresa_id = 1
            site_id = 1
        
        servicos = AdminModel.carregar_servicos(empresa_id, site_id)
        return jsonify({
            'sucesso': True,
            'servicos': servicos,
            'empresa_id': empresa_id,
            'site_id': site_id
        })
        
    except Exception as e:
        print(f"Erro ao buscar serviços: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/api/horarios_disponiveis')
def api_horarios_disponiveis():
    """Retorna horários disponíveis para uma data específica"""
    data_str = request.args.get('data')
    
    if not data_str:
        return jsonify({'erro': 'Data não informada'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar cronograma para a data e o usuário atual
        usuario_id = obter_usuario_id_atual()
        cursor.execute("""
            SELECT CRONOGRAMA FROM TESTE.AGENDA WHERE DATA = ? AND USUARIO_ID = ?
        """, (data_str, usuario_id))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if not resultado or not resultado[0]:
            return jsonify({'horarios': []})
        
        # Carregar o JSON do cronograma
        cronograma = json.loads(resultado[0]) if isinstance(resultado[0], str) else resultado[0]
        
        # Extrair horários disponíveis
        horarios_disponiveis = cronograma.get('horarios_disponiveis', [])
        
        # Filtrar apenas horários futuros (se for hoje)
        hoje = datetime.now().strftime('%Y-%m-%d')
        hora_atual = datetime.now().strftime('%H:%M')
        
        if data_str == hoje:
            horarios_disponiveis = [h for h in horarios_disponiveis if h > hora_atual]
        
        return jsonify({'horarios': horarios_disponiveis})
        
    except Exception as e:
        print(f"Erro ao buscar horários: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/api/agendar', methods=['POST'])
def api_agendar():
    """Salva um novo agendamento"""
    try:
        dados = request.json
        data_agendamento = dados.get('data')
        horario = dados.get('horario')
        servico = dados.get('servico')
        cliente_nome = dados.get('nome')
        cliente_telefone = dados.get('telefone')
        
        if not all([data_agendamento, horario, servico, cliente_nome, cliente_telefone]):
            return jsonify({'erro': 'Dados incompletos'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar o cronograma atual
        usuario_id = obter_usuario_id_atual()
        cursor.execute("""
            SELECT CRONOGRAMA FROM TESTE.AGENDA WHERE DATA = ? AND USUARIO_ID = ?
        """, (data_agendamento, usuario_id))
        
        resultado = cursor.fetchone()
        
        if not resultado or not resultado[0]:
            return jsonify({'erro': 'Data não disponível para agendamento'}), 400
        
        cronograma = json.loads(resultado[0]) if isinstance(resultado[0], str) else resultado[0]
        
        # Remover o horário selecionado dos disponíveis
        if horario in cronograma.get('horarios_disponiveis', []):
            cronograma['horarios_disponiveis'].remove(horario)
        
        # Adicionar o agendamento à lista de agendamentos
        if 'agendamentos' not in cronograma:
            cronograma['agendamentos'] = []
        
        novo_agendamento = {
            'cliente': cliente_nome,
            'telefone': cliente_telefone,
            'servico': servico,
            'horario': horario,
            'data_agendamento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        cronograma['agendamentos'].append(novo_agendamento)
        
        # Salvar o cronograma atualizado
        cronograma_json = json.dumps(cronograma)
        
        cursor.execute("""
            UPDATE TESTE.AGENDA 
            SET CRONOGRAMA = ?
            WHERE DATA = ? AND USUARIO_ID = ?
        """, (cronograma_json, data_agendamento, usuario_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'sucesso': True, 'mensagem': 'Agendamento realizado com sucesso!'})
        
    except Exception as e:
        print(f"Erro ao agendar: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/api/promocoes_cliente')
def api_promocoes_cliente():
    """Retorna promoções ativas para o cliente (site/empresa 1)"""
    try:
        from models import AdminModel
        promocoes = AdminModel.listar_promocoes(1, 1, apenas_ativas=True)
        return jsonify({'promocoes': promocoes})
    except Exception as e:
        print(f"Erro ao buscar promoções: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/api/imobiliaria/ofertas_cliente')
def api_imobiliaria_ofertas_cliente():
    """Retorna lista de ofertas ativas com pelo menos uma imagem para a imobiliária atual"""
    try:
        from models import AdminModel
        # Recuperar empresa_id e site_id da sessão
        cliente_atual = session.get('cliente_atual')
        if not cliente_atual:
            return jsonify({'sucesso': False, 'mensagem': 'Nenhum cliente ativo na sessão'}), 400
        
        empresa_id = cliente_atual.get('empresa_id')
        site_id = cliente_atual.get('site_id')
        
        if not empresa_id or not site_id:
            return jsonify({'sucesso': False, 'mensagem': 'Informações do cliente incompletas'}), 400
            
        ofertas = AdminModel.listar_ofertas(empresa_id, site_id)
        
        ofertas_filtradas = []
        for o in ofertas:
            # Filtrar apenas ofertas ativas
            if not o.get('ativo'):
                continue
            
            # Buscar os IDs das imagens da oferta
            imagens_ids = AdminModel.listar_id_imagens_oferta(o['id'])
            
            # Filtrar apenas ofertas que possuam pelo menos uma imagem cadastrada
            if len(imagens_ids) == 0:
                continue
                
            o['imagens_ids'] = imagens_ids
            ofertas_filtradas.append(o)
            
        return jsonify({'sucesso': True, 'ofertas': ofertas_filtradas})
        
    except Exception as e:
        print(f"Erro ao buscar ofertas de imobiliária: {e}")
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

# ==================== ROTAS DE IMAGENS (BLOB DO BANCO) ====================

@app.route('/img/oferta/<int:oferta_id>/<int:indice>')
def renderizar_imagem_oferta(oferta_id, indice):
    try:
        from models import AdminModel
        binario = AdminModel.buscar_imagem_oferta(oferta_id, indice)
        if binario:
            return send_file(
                io.BytesIO(binario),
                mimetype='image/jpeg',
                as_attachment=False,
                download_name=f'oferta_{oferta_id}_{indice}.jpg'
            )
        return "Not found", 404
    except Exception as e:
        print(f"Erro ao renderizar imagem de oferta: {e}")
        return "Internal error", 500

@app.route('/img/servico/<int:empresa_id>/<int:site_id>/<int:servico_id>/<int:indice>')
def renderizar_imagem_servico(empresa_id, site_id, servico_id, indice):
    try:
        from models import AdminModel
        binario = AdminModel.buscar_imagem_servico(empresa_id, site_id, servico_id, indice)
        if binario:
            return send_file(
                io.BytesIO(binario),
                mimetype='image/jpeg',
                as_attachment=False,
                download_name=f'servico_{servico_id}_{indice}.jpg'
            )
        return "Not found", 404
    except Exception as e:
        print(f"Erro ao renderizar imagem de servico: {e}")
        return "Internal error", 500

@app.route('/img/logo/<int:empresa_id>/<int:site_id>')
def renderizar_logo(empresa_id, site_id):
    try:
        from models import AdminModel
        binario = AdminModel.buscar_logo(empresa_id, site_id)
        if binario:
            return send_file(
                io.BytesIO(binario),
                mimetype='image/png',
                as_attachment=False,
                download_name=f'logo_{empresa_id}_{site_id}.png'
            )
        return "Not found", 404
    except Exception as e:
        print(f"Erro ao renderizar logo: {e}")
        return "Internal error", 500

# ==================== ROTAS PARA URL AMIGÁVEL ====================
@app.route('/<string:url_cliente>')
def home_cliente_url(url_cliente):
    """Página inicial do cliente via URL amigável (ex: /marcus-teste)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT C.ID, C.NOME_FANTASIA, C.COR_PRIMARIA, C.COR_SECUNDARIA, C.COR_TERCIARIA,
                   C.LOGO_URL, C.WHATSAPP_NUMERO, C.URL_AMIGAVEL,
                   U.EMPRESA_ID, U.SITE_ID, C.LAYOUT_CONFIG, U.PERSONALIZAR_APARENCIA, U.ATIVO,
                   E.ENDERECO
            FROM TESTE.CLIENTES C
            JOIN TESTE.USUARIOS U ON C.USUARIO_ID = U.ID
            LEFT JOIN TESTE.EMPRESA E ON U.EMPRESA_ID = E.ID
            WHERE C.URL_AMIGAVEL = ?
        """, (url_cliente,))
        
        cliente = cursor.fetchone()
        conn.close()
        
        if cliente:
            ativo = cliente[12] if len(cliente) > 12 else 'S'
            if ativo == 'N':
                whatsapp = cliente[6]
                return render_template_string(SUSPENSION_TEMPLATE, whatsapp=whatsapp)
                
            layout_config = merge_layout_config(cliente[10] if len(cliente) > 10 else None)
            
            # Extrair título e corpo customizados do site a partir da permissão de aparência do usuário
            aparencia_config = {}
            titulo_site = ''
            corpo_site = ''
            if len(cliente) > 11 and cliente[11]:
                try:
                    aparencia_config = json.loads(cliente[11])
                    titulo_site = aparencia_config.get('titulo_site', '')
                    corpo_site = aparencia_config.get('corpo_site', '')
                except Exception as e:
                    print(f"Erro ao parsear personalizar_aparencia: {e}")
                    
            empresa_id = cliente[8]
            site_id = cliente[9]
            endereco = cliente[13] if len(cliente) > 13 else None
            from models import AdminModel
            if AdminModel.verificar_existe_logo(empresa_id, site_id):
                logo_url = f"/img/logo/{empresa_id}/{site_id}"
            else:
                logo_url = cliente[5]
 
            # Salvar na sessão qual cliente está sendo acessado
            session['cliente_atual'] = {
                'id': cliente[0],
                'nome': cliente[1],
                'cor_primaria': cliente[2] if cliente[2] else '#667eea',
                'cor_secundaria': cliente[3] if cliente[3] else '#764ba2',
                'cor_terciaria': cliente[4] if cliente[4] else '#48bb78',
                'logo_url': logo_url,
                'whatsapp': cliente[6],
                'url_amigavel': cliente[7],
                'empresa_id': empresa_id,
                'site_id': site_id,
                'layout_config': layout_config,
                'empresa_endereco': endereco
            }
            
            # Se o site_id for 4 (Imobiliária), renderiza o template da imobiliária
            if cliente[9] == 4:
                return render_template('cliente_imobiliaria.html',
                                       cliente_nome=cliente[1],
                                       cor_primaria=cliente[2] if cliente[2] else '#667eea',
                                       cor_secundaria=cliente[3] if cliente[3] else '#764ba2',
                                       whatsapp=cliente[6],
                                       logo_url=logo_url,
                                       layout_config=layout_config,
                                       titulo_site=titulo_site,
                                       corpo_site=corpo_site)
            
            return render_template('cliente_home.html', 
                                   cliente_nome=cliente[1],
                                   cor_primaria=cliente[2] if cliente[2] else '#667eea',
                                   cor_secundaria=cliente[3] if cliente[3] else '#764ba2',
                                   whatsapp=cliente[6],
                                   logo_url=logo_url,
                                   layout_config=layout_config,
                                   titulo_site=titulo_site,
                                   corpo_site=corpo_site,
                                   aparencia_config=aparencia_config,
                                   empresa_endereco=endereco)
        
        # Se não encontrar, vai para o padrão
        return render_template('cliente_home.html', 
                               cliente_nome='Salão de Beleza',
                               cor_primaria='#667eea',
                               cor_secundaria='#764ba2',
                               whatsapp=None,
                               logo_url=None,
                               layout_config={},
                               titulo_site='',
                               corpo_site='',
                               aparencia_config={})
    except Exception as e:
        print(f"Erro ao carregar cliente: {e}")
        return render_template('cliente_home.html', 
                               cliente_nome='Salão de Beleza',
                               cor_primaria='#667eea',
                               cor_secundaria='#764ba2',
                               whatsapp=None,
                               logo_url=None,
                               layout_config={},
                               titulo_site='',
                               corpo_site='',
                               aparencia_config={})

@app.route('/<string:url_cliente>/agendamento')
def agendamento_cliente_url(url_cliente):
    """Página de agendamento do cliente via URL amigável"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT U.ATIVO 
            FROM TESTE.CLIENTES C 
            JOIN TESTE.USUARIOS U ON C.USUARIO_ID = U.ID 
            WHERE C.URL_AMIGAVEL = ?
        """, (url_cliente,))
        row = cursor.fetchone()
        conn.close()
        if row and row[0] == 'N':
            return redirect(url_for('home_cliente_url', url_cliente=url_cliente))
            
    if 'cliente_atual' not in session or session['cliente_atual'].get('url_amigavel') != url_cliente:
        return redirect(url_for('home_cliente_url', url_cliente=url_cliente))
    
    # Certificar que layout_config está preenchido
    if 'layout_config' not in session['cliente_atual']:
        session['cliente_atual']['layout_config'] = {}
        
    return render_template('agendamento.html', 
                          cliente=session['cliente_atual'])

@app.route('/<string:url_cliente>/admin')
def admin_cliente_url(url_cliente):
    """Acesso admin via URL amigável (ex: /marcus-teste/admin)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT U.ID, U.NOME, U.EMAIL, U.TIPO, U.SENHA, U.EMPRESA_ID, U.SITE_ID, C.ID,
               C.NOME_FANTASIA, C.COR_PRIMARIA, C.COR_SECUNDARIA, C.COR_TERCIARIA, C.LOGO_URL, 
               C.WHATSAPP_NUMERO, C.URL_AMIGAVEL, U.ATIVO
        FROM TESTE.CLIENTES C
        JOIN TESTE.USUARIOS U ON C.USUARIO_ID = U.ID
        WHERE C.URL_AMIGAVEL = ?
    """, (url_cliente,))
    
    usuario = cursor.fetchone()
    conn.close()
    
    if usuario:
        ativo = usuario[15] if len(usuario) > 15 else 'S'
        tipo = usuario[3]
        if tipo != 'proprietario' and ativo == 'N':
            return render_template("admin_login.html", erro="Seu acesso está suspenso. Entre em contato com a administração.")
            
        session['admin_id'] = usuario[0]
        session['admin_nome'] = usuario[1]
        session['admin_email'] = usuario[2]
        session['tipo'] = usuario[3]
        session['empresa_id'] = usuario[5] if usuario[5] else 1
        session['site_id'] = usuario[6] if usuario[6] else 1
        session['cliente_id'] = usuario[7]
        session['cliente_nome'] = usuario[8] if usuario[8] else usuario[1]
        session['cliente_cor_primaria'] = usuario[9] if usuario[9] else '#667eea'
        session['cliente_cor_secundaria'] = usuario[10] if usuario[10] else '#764ba2'
        session['cliente_cor_terciaria'] = usuario[11] if usuario[11] else '#48bb78'
        session['cliente_logo_url'] = usuario[12]
        session['cliente_whatsapp'] = usuario[13]
        session['cliente_url'] = usuario[14]
        
        return redirect('/admin/dashboard')
    
    return redirect('/admin/login')
    

@app.route('/api/buscar_agendamentos_cliente')
def api_buscar_agendamentos_cliente():
    telefone = request.args.get('telefone')
    if not telefone:
        return jsonify({'erro': 'Telefone não informado'}), 400
    
    # Limpar telefone do input para comparação (remover parênteses, traços, espaços)
    tel_limpo = ''.join(c for c in telefone if c.isdigit())
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar cronogramas de hoje para frente filtrando pelo usuário atual
        usuario_id = obter_usuario_id_atual()
        cursor.execute("""
            SELECT DATA, CRONOGRAMA FROM TESTE.AGENDA 
            WHERE DATA >= CAST(GETDATE() AS DATE) AND USUARIO_ID = ?
            ORDER BY DATA
        """, (usuario_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        agendamentos_encontrados = []
        for row in rows:
            data_str = row[0].strftime('%Y-%m-%d')
            if row[1]:
                cronograma = json.loads(row[1]) if isinstance(row[1], str) else row[1]
                agendamentos = cronograma.get('agendamentos', [])
                for ag in agendamentos:
                    tel_ag_limpo = ''.join(c for c in ag.get('telefone', '') if c.isdigit())
                    # Comparação de telefone (se bater o final ou exato para tolerar DDDs ou ddd digitados)
                    if tel_ag_limpo == tel_limpo or tel_ag_limpo.endswith(tel_limpo) or tel_limpo.endswith(tel_ag_limpo):
                        servico = ag.get('servico', {})
                        servico_nome = servico.get('nome') if isinstance(servico, dict) else servico
                        agendamentos_encontrados.append({
                            'data': data_str,
                            'horario': ag.get('horario'),
                            'cliente': ag.get('cliente'),
                            'telefone': ag.get('telefone'),
                            'servico': servico_nome
                        })
                        
        agendamentos_encontrados.sort(key=lambda x: (x['data'], x['horario']))
        return jsonify({'agendamentos': agendamentos_encontrados})
    except Exception as e:
        print(f"Erro ao buscar agendamentos do cliente: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/api/desmarcar_agendamento_cliente', methods=['POST'])
def api_desmarcar_agendamento_cliente():
    try:
        dados = request.json
        data_ag = dados.get('data')
        horario = dados.get('horario')
        telefone = dados.get('telefone')
        
        if not all([data_ag, horario, telefone]):
            return jsonify({'erro': 'Dados incompletos'}), 400
            
        tel_limpo = ''.join(c for c in telefone if c.isdigit())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar cronograma
        usuario_id = obter_usuario_id_atual()
        cursor.execute("SELECT CRONOGRAMA FROM TESTE.AGENDA WHERE DATA = ? AND USUARIO_ID = ?", (data_ag, usuario_id))
        row = cursor.fetchone()
        
        if not row or not row[0]:
            conn.close()
            return jsonify({'erro': 'Agenda não encontrada'}), 404
            
        cronograma = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        agendamentos = cronograma.get('agendamentos', [])
        
        # Achar o agendamento a ser removido
        encontrado = None
        for ag in agendamentos:
            tel_ag_limpo = ''.join(c for c in ag.get('telefone', '') if c.isdigit())
            if ag.get('horario') == horario and (tel_ag_limpo == tel_limpo or tel_ag_limpo.endswith(tel_limpo) or tel_limpo.endswith(tel_ag_limpo)):
                encontrado = ag
                break
                
        if not encontrado:
            conn.close()
            return jsonify({'erro': 'Agendamento não encontrado para desmarcar'}), 404
            
        # Remover o agendamento
        agendamentos.remove(encontrado)
        
        # Adicionar o horário de volta aos disponíveis (e ordenar)
        horarios_disp = cronograma.get('horarios_disponiveis', [])
        if horario not in horarios_disp:
            horarios_disp.append(horario)
            horarios_disp.sort()
            
        cronograma['agendamentos'] = agendamentos
        cronograma['horarios_disponiveis'] = horarios_disp
        
        # Salvar no banco
        cursor.execute("""
            UPDATE TESTE.AGENDA 
            SET CRONOGRAMA = ?
            WHERE DATA = ? AND USUARIO_ID = ?
        """, (json.dumps(cronograma), data_ag, usuario_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'sucesso': True, 'mensagem': 'Agendamento cancelado com sucesso!'})
        
    except Exception as e:
        print(f"Erro ao desmarcar agendamento: {e}")
        return jsonify({'erro': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)