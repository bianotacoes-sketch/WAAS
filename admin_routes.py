from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from models import AdminModel
from db_config import get_db_connection
import json
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
def check_user_active():
    # Exclude login and logout endpoints
    if request.path.endswith('/login') or request.path.endswith('/logout'):
        return
        
    if 'admin_id' in session:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ATIVO, TIPO FROM TESTE.USUARIOS WHERE ID = ?", (session['admin_id'],))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                ativo = row[0]
                tipo = row[1]
                if tipo != 'proprietario' and ativo == 'N':
                    session.clear()
                    return render_template("admin_login.html", erro="Seu acesso está suspenso. Entre em contato com a administração.")

# ==================== ROTAS ====================

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        admin = AdminModel.autenticar_admin(email, senha)
        if admin:
            if admin.get('suspenso'):
                return render_template("admin_login.html", erro="Seu acesso está suspenso. Entre em contato com a administração.")
            session['admin_id'] = admin['id']
            session['admin_nome'] = admin['nome']
            session['admin_email'] = admin['email']
            session['empresa_id'] = admin.get('empresa_id', 1)
            session['site_id'] = admin.get('site_id', 1)
            session['tipo'] = admin.get('tipo', 'user')
            
            # Adicionar dados do cliente na sessão
            session['cliente_id'] = admin.get('cliente_id')
            session['cliente_nome'] = admin.get('cliente_nome', admin['nome'])
            session['cliente_cor_primaria'] = admin.get('cliente_cor_primaria', '#667eea')
            session['cliente_cor_secundaria'] = admin.get('cliente_cor_secundaria', '#764ba2')
            session['cliente_cor_terciaria'] = admin.get('cliente_cor_terciaria', '#48bb78')
            session['cliente_logo_url'] = admin.get('cliente_logo_url')
            session['cliente_whatsapp'] = admin.get('cliente_whatsapp')
            session['cliente_url'] = admin.get('cliente_url')
            
            if admin.get('tipo') == 'proprietario':
                return redirect(url_for('admin.proprietario_dashboard'))
            return redirect(url_for('admin.dashboard'))
        return render_template("admin_login.html", erro="Email ou senha inválidos")
    return render_template("admin_login.html")

@admin_bp.route('/dashboard')
def dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    # Buscar permissões do usuário
    permissoes = AdminModel.buscar_permissoes_usuario(session['admin_id'])
    
    # Dados do cliente da sessão
    cliente = {
        'nome_fantasia': session.get('cliente_nome', session['admin_nome']),
        'cor_primaria': session.get('cliente_cor_primaria', '#667eea'),
        'cor_secundaria': session.get('cliente_cor_secundaria', '#764ba2'),
        'cor_terciaria': session.get('cliente_cor_terciaria', '#48bb78'),
        'logo_url': session.get('cliente_logo_url'),
        'whatsapp': session.get('cliente_whatsapp'),
        'url_amigavel': session.get('cliente_url')
    }
    
    return render_template("admin_dashboard.html", 
                                  admin_nome=session['admin_nome'],
                                  nome_dashboard=permissoes.get('nome_dashboard', {}),
                                  config_agenda=permissoes.get('configurar_agenda', {}),
                                  gerenciar_servico=permissoes.get('gerenciar_servico', {}),
                                  promocoes=permissoes.get('promocoes', {}),
                                  gerenciar_clientes=permissoes.get('gerenciar_clientes', {}),
                                  personalizar_aparencia=permissoes.get('personalizar_aparencia', {}),
                                  gerenciar_ofertas=permissoes.get('gerenciar_ofertas', {}),
                                  imagens_servicos=permissoes.get('imagens_servicos', {}),
                                  cores=cliente,
                                  cliente=cliente)

@admin_bp.route('/agenda')
def agenda():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    cliente = {
        'nome_fantasia': session.get('cliente_nome', session['admin_nome']),
        'cor_primaria': session.get('cliente_cor_primaria', '#667eea'),
        'cor_secundaria': session.get('cliente_cor_secundaria', '#764ba2'),
        'cor_terciaria': session.get('cliente_cor_terciaria', '#48bb78'),
        'logo_url': session.get('cliente_logo_url'),
        'whatsapp': session.get('cliente_whatsapp'),
        'url_amigavel': session.get('cliente_url')
    }
    return render_template('admin_agenda.html', admin_nome=session['admin_nome'], data_referencia=datetime.now().strftime('%Y-%m-%d'), cores=cliente, cliente=cliente)

@admin_bp.route('/servicos')
def servicos():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    cliente = {
        'nome_fantasia': session.get('cliente_nome', session['admin_nome']),
        'cor_primaria': session.get('cliente_cor_primaria', '#667eea'),
        'cor_secundaria': session.get('cliente_cor_secundaria', '#764ba2'),
        'cor_terciaria': session.get('cliente_cor_terciaria', '#48bb78'),
        'logo_url': session.get('cliente_logo_url'),
        'whatsapp': session.get('cliente_whatsapp'),
        'url_amigavel': session.get('cliente_url')
    }
    return render_template('admin_servicos.html', admin_nome=session['admin_nome'], cores=cliente, cliente=cliente)

@admin_bp.route('/promocoes')
def promocoes():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    cliente = {
        'nome_fantasia': session.get('cliente_nome', session['admin_nome']),
        'cor_primaria': session.get('cliente_cor_primaria', '#667eea'),
        'cor_secundaria': session.get('cliente_cor_secundaria', '#764ba2'),
        'cor_terciaria': session.get('cliente_cor_terciaria', '#48bb78'),
        'logo_url': session.get('cliente_logo_url'),
        'whatsapp': session.get('cliente_whatsapp'),
        'url_amigavel': session.get('cliente_url')
    }
    return render_template('admin_promocoes.html', admin_nome=session['admin_nome'], cores=cliente, cliente=cliente)

@admin_bp.route('/proprietario')
def proprietario_dashboard():
    """Dashboard do proprietário para gerenciar usuários, empresas e sites"""
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    if session.get('tipo') != 'proprietario':
        return redirect(url_for('admin.dashboard'))
    
    return render_template('proprietario_dashboard.html', admin_nome=session['admin_nome'])

# ==================== APIs ====================

@admin_bp.route('/api/servicos', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_servicos():
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    
    empresa_id = session.get('empresa_id', 1)
    site_id = session.get('site_id', 1)
    
    if request.method == 'GET':
        servicos = AdminModel.carregar_servicos(empresa_id, site_id)
        return jsonify({'sucesso': True, 'servicos': servicos})
    elif request.method == 'POST':
        novo_servico = request.json
        resultado = AdminModel.adicionar_servico(empresa_id, site_id, novo_servico)
        return jsonify({'sucesso': resultado})
    elif request.method == 'PUT':
        data = request.json
        resultado = AdminModel.editar_servico(empresa_id, site_id, data['index'], data['servico'])
        return jsonify({'sucesso': resultado})
    elif request.method == 'DELETE':
        data = request.json
        resultado = AdminModel.excluir_servico(empresa_id, site_id, data['index'])
        return jsonify({'sucesso': resultado})

@admin_bp.route('/api/carregar_cronograma', methods=['GET'])
def api_carregar_cronograma():
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    data_inicio = request.args.get('data_inicio')
    return jsonify({'cronograma': AdminModel.carregar_cronograma_semanal(data_inicio)})

@admin_bp.route('/api/salvar_semana', methods=['POST'])
def api_salvar_semana():
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    dados = request.json
    resultado = AdminModel.salvar_cronograma_semanal(dados.get('data_inicio'), dados.get('config_semana'))
    return jsonify({'sucesso': resultado, 'mensagem': 'Salvo com sucesso!' if resultado else 'Erro ao salvar'})

@admin_bp.route('/api/promocoes', methods=['GET', 'POST'])
def api_promocoes():
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    empresa_id = session.get('empresa_id', 1)
    site_id = session.get('site_id', 1)
    if request.method == 'GET':
        promocoes = AdminModel.listar_promocoes(empresa_id, site_id, apenas_ativas=False)
        return jsonify({'sucesso': True, 'promocoes': promocoes})
    elif request.method == 'POST':
        dados = request.json
        resultado = AdminModel.salvar_promocao(empresa_id, site_id, dados)
        return jsonify({'sucesso': resultado})

@admin_bp.route('/api/promocoes/<int:promo_id>/alternar', methods=['PUT'])
def api_alternar_promocao(promo_id):
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    ativa = request.json.get('ativa', False)
    empresa_id = session.get('empresa_id', 1)
    site_id = session.get('site_id', 1)
    resultado = AdminModel.alternar_ativa_promocao(empresa_id, site_id, promo_id, ativa)
    return jsonify({'sucesso': resultado})

@admin_bp.route('/api/promocoes/<int:promo_id>', methods=['DELETE'])
def api_excluir_promocao(promo_id):
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    empresa_id = session.get('empresa_id', 1)
    site_id = session.get('site_id', 1)
    resultado = AdminModel.excluir_promocao(empresa_id, site_id, promo_id)
    return jsonify({'sucesso': resultado})

# ==================== APIs DO PROPRIETÁRIO ====================
@admin_bp.route('/api/proprietario/empresas', methods=['GET', 'POST', 'DELETE'])
def api_proprietario_empresas():
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    
    if session.get('tipo') != 'proprietario':
        return jsonify({'erro': 'Permissão negada'}), 403
    
    if request.method == 'GET':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ID, NOME, ENDERECO FROM TESTE.EMPRESA ORDER BY ID")
        empresas = [{'id': row[0], 'nome': row[1], 'endereco': row[2] or ''} for row in cursor.fetchall()]
        conn.close()
        return jsonify({'empresas': empresas})
    
    elif request.method == 'POST':
        dados = request.json
        nome = dados.get('nome')
        endereco = dados.get('endereco', '')
        if not nome:
            return jsonify({'erro': 'Nome da empresa é obrigatório'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM TESTE.EMPRESA WHERE NOME = ?", (nome,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({'erro': 'Já existe uma empresa com este nome'}), 400
        
        cursor.execute("INSERT INTO TESTE.EMPRESA (NOME, ENDERECO) VALUES (?, ?)", (nome, endereco))
        conn.commit()
        novo_id = cursor.lastrowid
        conn.close()
        return jsonify({'sucesso': True, 'id': novo_id, 'mensagem': 'Empresa criada com sucesso!'})
    
    elif request.method == 'DELETE':
        empresa_id = request.args.get('id')
        if not empresa_id:
            return jsonify({'erro': 'ID da empresa é obrigatório'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM TESTE.USUARIOS WHERE EMPRESA_ID = ?", (empresa_id,))
        count = cursor.fetchone()[0]
        if count > 0:
            conn.close()
            return jsonify({'erro': f'Não é possível excluir. Existem {count} usuários vinculados a esta empresa.'}), 400
        
        cursor.execute("DELETE FROM TESTE.EMPRESA WHERE ID = ?", (empresa_id,))
        conn.commit()
        conn.close()
        return jsonify({'sucesso': True, 'mensagem': 'Empresa excluída com sucesso!'})

@admin_bp.route('/api/proprietario/sites', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_proprietario_sites():
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    
    if session.get('tipo') != 'proprietario':
        return jsonify({'erro': 'Permissão negada'}), 403
    
    if request.method == 'GET':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ID, NOME FROM TESTE.SITE ORDER BY ID")
        sites = [{'id': row[0], 'nome': row[1]} for row in cursor.fetchall()]
        conn.close()
        return jsonify({'sites': sites})
    
    elif request.method == 'POST':
        dados = request.json
        nome = dados.get('nome')
        
        if not nome:
            return jsonify({'erro': 'Nome do site é obrigatório'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO TESTE.SITE (NOME) VALUES (?)", (nome,))
        conn.commit()
        novo_id = cursor.lastrowid
        conn.close()
        return jsonify({'sucesso': True, 'id': novo_id, 'mensagem': 'Site criado com sucesso!'})
    
    elif request.method == 'PUT':
        dados = request.json
        site_id = dados.get('id')
        novo_nome = dados.get('nome')
        
        if not site_id or not novo_nome:
            return jsonify({'erro': 'ID e novo nome são obrigatórios'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE TESTE.SITE SET NOME = ? WHERE ID = ?", (novo_nome, site_id))
        conn.commit()
        conn.close()
        return jsonify({'sucesso': True, 'mensagem': 'Site atualizado com sucesso!'})
    
    elif request.method == 'DELETE':
        site_id = request.args.get('id')
        if not site_id:
            return jsonify({'erro': 'ID do site é obrigatório'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM TESTE.USUARIOS WHERE SITE_ID = ?", (site_id,))
        count = cursor.fetchone()[0]
        if count > 0:
            conn.close()
            return jsonify({'erro': f'Não é possível excluir. Existem {count} usuários vinculados a este site.'}), 400
        
        cursor.execute("DELETE FROM TESTE.SITE WHERE ID = ?", (site_id,))
        conn.commit()
        conn.close()
        return jsonify({'sucesso': True, 'mensagem': 'Site excluído com sucesso!'})

@admin_bp.route('/api/proprietario/usuarios', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_proprietario_usuarios():
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    
    if session.get('tipo') != 'proprietario':
        return jsonify({'erro': 'Permissão negada'}), 403
    
    if request.method == 'GET':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID, NOME, EMAIL, TIPO, EMPRESA_ID, SITE_ID, ATIVO 
            FROM TESTE.USUARIOS 
            WHERE TIPO != 'proprietario'
            ORDER BY ID
        """)
        usuarios = []
        for row in cursor.fetchall():
            usuarios.append({
                'id': row[0],
                'nome': row[1],
                'email': row[2],
                'tipo': row[3],
                'empresa_id': row[4],
                'site_id': row[5],
                'ativo': row[6] if len(row) > 6 and row[6] else 'S'
            })
        conn.close()
        return jsonify({'usuarios': usuarios})
    
    elif request.method == 'POST':
        dados = request.json
        nome = dados.get('nome')
        email = dados.get('email')
        senha = dados.get('senha')
        tipo = dados.get('tipo')
        empresa_id = dados.get('empresa_id')
        site_id = dados.get('site_id')
        ativo = dados.get('ativo', 'S')
        
        if not all([nome, email, senha, tipo]):
            return jsonify({'erro': 'Nome, email, senha e tipo são obrigatórios'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM TESTE.USUARIOS WHERE EMAIL = ?", (email,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({'erro': 'Este email já está cadastrado'}), 400
        
        cursor.execute("""
            INSERT INTO TESTE.USUARIOS (NOME, EMAIL, SENHA, TIPO, EMPRESA_ID, SITE_ID, ATIVO)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nome, email, senha, tipo, empresa_id, site_id, ativo))
        conn.commit()
        conn.close()
        return jsonify({'sucesso': True, 'mensagem': 'Usuário criado com sucesso!'})
    
    elif request.method == 'PUT':
        dados = request.json
        usuario_id = dados.get('id')
        nome = dados.get('nome')
        email = dados.get('email')
        tipo = dados.get('tipo')
        empresa_id = dados.get('empresa_id')
        site_id = dados.get('site_id')
        senha = dados.get('senha')
        ativo = dados.get('ativo', 'S')
        
        if not usuario_id or not nome or not email or not tipo:
            return jsonify({'erro': 'Dados incompletos'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM TESTE.USUARIOS WHERE EMAIL = ? AND ID != ?", (email, usuario_id))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({'erro': 'Este email já está em uso por outro usuário'}), 400
        
        if senha:
            cursor.execute("""
                UPDATE TESTE.USUARIOS 
                SET NOME = ?, EMAIL = ?, TIPO = ?, EMPRESA_ID = ?, SITE_ID = ?, SENHA = ?, ATIVO = ?
                WHERE ID = ?
            """, (nome, email, tipo, empresa_id, site_id, senha, ativo, usuario_id))
        else:
            cursor.execute("""
                UPDATE TESTE.USUARIOS 
                SET NOME = ?, EMAIL = ?, TIPO = ?, EMPRESA_ID = ?, SITE_ID = ?, ATIVO = ?
                WHERE ID = ?
            """, (nome, email, tipo, empresa_id, site_id, ativo, usuario_id))
        
        conn.commit()
        conn.close()
        return jsonify({'sucesso': True, 'mensagem': 'Usuário atualizado com sucesso!'})
    
    elif request.method == 'DELETE':
        usuario_id = request.args.get('id')
        if not usuario_id:
            return jsonify({'erro': 'ID do usuário é obrigatório'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM TESTE.USUARIOS WHERE ID = ? AND TIPO != 'proprietario'", (usuario_id,))
        conn.commit()
        conn.close()
        return jsonify({'sucesso': True, 'mensagem': 'Usuário excluído com sucesso!'})

@admin_bp.route('/api/proprietario/empresa/atualizar', methods=['PUT'])
def api_proprietario_atualizar_empresa():
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    
    if session.get('tipo') != 'proprietario':
        return jsonify({'erro': 'Permissão negada'}), 403
    
    dados = request.json
    empresa_id = dados.get('id')
    novo_nome = dados.get('nome')
    novo_endereco = dados.get('endereco', '')
    
    if not empresa_id or not novo_nome:
        return jsonify({'erro': 'ID e novo nome são obrigatórios'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE TESTE.EMPRESA SET NOME = ?, ENDERECO = ? WHERE ID = ?", (novo_nome, novo_endereco, empresa_id))
    conn.commit()
    conn.close()
    return jsonify({'sucesso': True, 'mensagem': 'Empresa atualizada com sucesso!'})

# ==================== NOVAS APIs DO PROPRIETÁRIO (Personalização) ====================

@admin_bp.route('/api/proprietario/clientes', methods=['GET'])
def api_proprietario_clientes():
    """Lista todos os clientes para o proprietário"""
    if 'admin_id' not in session or session.get('tipo') != 'proprietario':
        return jsonify({'erro': 'Não autorizado'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT C.ID, COALESCE(C.NOME_FANTASIA, U.NOME), C.URL_AMIGAVEL, C.COR_PRIMARIA, C.COR_SECUNDARIA, 
               C.COR_TERCIARIA, C.LOGO_URL, C.WHATSAPP_NUMERO, C.ATIVO,
               U.NOME as USUARIO_NOME, U.EMAIL as USUARIO_EMAIL, U.ID as USUARIO_ID
        FROM TESTE.USUARIOS U
        LEFT JOIN TESTE.CLIENTES C ON C.USUARIO_ID = U.ID
        WHERE U.TIPO != 'proprietario'
        ORDER BY U.ID
    """)
    
    clientes = []
    for row in cursor.fetchall():
        clientes.append({
            'id': row[0],
            'nome_fantasia': row[1],
            'url_amigavel': row[2],
            'cor_primaria': row[3],
            'cor_secundaria': row[4],
            'cor_terciaria': row[5],
            'logo_url': row[6],
            'whatsapp': row[7],
            'ativo': row[8],
            'usuario_nome': row[9],
            'usuario_email': row[10],
            'usuario_id': row[11]
        })
    conn.close()
    return jsonify({'clientes': clientes})

@admin_bp.route('/api/proprietario/clientes/personalizar', methods=['PUT'])
def api_proprietario_personalizar_cliente():
    """Personaliza layout do cliente"""
    if 'admin_id' not in session or session.get('tipo') != 'proprietario':
        return jsonify({'erro': 'Não autorizado'}), 401
    
    dados = request.json
    usuario_id = dados.get('usuario_id')
    
    if not usuario_id:
        return jsonify({'erro': 'usuario_id não fornecido'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT ID FROM TESTE.CLIENTES WHERE USUARIO_ID = ?", (usuario_id,))
    cliente_existe = cursor.fetchone()
    
    if cliente_existe:
        cursor.execute("""
            UPDATE TESTE.CLIENTES 
            SET NOME_FANTASIA = ?,
                COR_PRIMARIA = ?,
                COR_SECUNDARIA = ?,
                COR_TERCIARIA = ?,
                LOGO_URL = ?,
                WHATSAPP_NUMERO = ?,
                URL_AMIGAVEL = ?
            WHERE USUARIO_ID = ?
        """, (
            dados.get('nome_fantasia'),
            dados.get('cor_primaria', '#667eea'),
            dados.get('cor_secundaria', '#764ba2'),
            dados.get('cor_terciaria', '#48bb78'),
            dados.get('logo_url'),
            dados.get('whatsapp'),
            dados.get('url_amigavel'),
            usuario_id
        ))
    else:
        cursor.execute("""
            INSERT INTO TESTE.CLIENTES (USUARIO_ID, NOME_FANTASIA, COR_PRIMARIA, COR_SECUNDARIA, COR_TERCIARIA, LOGO_URL, WHATSAPP_NUMERO, URL_AMIGAVEL)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            usuario_id,
            dados.get('nome_fantasia'),
            dados.get('cor_primaria', '#667eea'),
            dados.get('cor_secundaria', '#764ba2'),
            dados.get('cor_terciaria', '#48bb78'),
            dados.get('logo_url'),
            dados.get('whatsapp'),
            dados.get('url_amigavel')
        ))
        
    conn.commit()
    conn.close()
    return jsonify({'sucesso': True, 'mensagem': 'Layout personalizado com sucesso!'})

@admin_bp.route('/api/proprietario/usuarios/<int:usuario_id>/permissoes', methods=['GET'])
def api_proprietario_buscar_permissoes(usuario_id):
    """Busca as permissões de um usuário"""
    if 'admin_id' not in session or session.get('tipo') != 'proprietario':
        return jsonify({'erro': 'Não autorizado'}), 401
    
    permissoes = AdminModel.buscar_permissoes_usuario(usuario_id)
    return jsonify({'sucesso': True, 'permissoes': permissoes})

@admin_bp.route('/api/proprietario/usuarios/permissoes', methods=['PUT'])
def api_proprietario_atualizar_permissoes():
    """Atualiza as permissões JSON de um usuário"""
    if 'admin_id' not in session or session.get('tipo') != 'proprietario':
        return jsonify({'erro': 'Não autorizado'}), 401
    
    dados = request.json
    usuario_id = dados.get('usuario_id')
    permissoes = dados.get('permissoes', {})
    
    resultado = AdminModel.atualizar_permissoes_usuario(usuario_id, permissoes)
    return jsonify({'sucesso': resultado, 'mensagem': 'Permissões atualizadas!'})

# ==================== ROTAS DE CUSTOMIZAÇÃO VISUAL ====================

DEFAULT_LAYOUT = {
    'preset_atual': 'salao',
    'cor_destaque': '#10b981',
    'cor_fundo_geral': '#0f172a',
    'cor_fundo_header': 'rgba(30, 41, 59, 0.8)',
    'cor_fundo_hero': 'transparent',
    'cor_texto_principal': '#f8fafc',
    'cor_texto_secundario': '#94a3b8',
    'cor_botao_primario': 'linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%)',
    'cor_botao_secundario': 'transparent',
    'cor_botao_hover': 'linear-gradient(135deg, var(--primary) 10%, var(--secondary) 90%)',
    'cor_bordas': '#334155',
    'cor_cards': '#1e293b',
    'header_style': 'sticky',
    'hero_align': 'center',
    'bg_type': 'gradient',
    'bg_image_url': '',
    'border_radius_btn': '50px',
    'border_radius_card': '24px',
    'shadow_intensity': 'normal',
    'spacing_main': 'normal',
    'show_hero_badge': True,
    'hero_badge_text': 'Atendimento Exclusivo',
    'show_hero_secondary_btn': True,
    'hero_secondary_btn_text': 'Ver Serviços',
    'show_header_whatsapp': True,
    'show_float_whatsapp': True,
    'font_base': 'Inter',
    'font_title': 'Outfit',
    'title_size': '52px',
    'title_weight': '800',
    'subtitle_size': '18px'
}

def merge_layout_config(saved_config):
    config = DEFAULT_LAYOUT.copy()
    if saved_config:
        try:
            parsed = json.loads(saved_config) if isinstance(saved_config, str) else saved_config
            if isinstance(parsed, dict):
                config.update(parsed)
        except Exception as e:
            print(f"Erro ao parsear layout_config: {e}")
    return config

@admin_bp.route('/layout')
def layout():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
        
    # Verificar permissão do usuário
    if session.get('tipo') != 'proprietario':
        permissoes = AdminModel.buscar_permissoes_usuario(session['admin_id'])
        if not permissoes.get('personalizar_aparencia', {}).get('ativo', False):
            return redirect(url_for('admin.dashboard'))
            
    cliente_id = None
    if session.get('tipo') == 'proprietario':
        cliente_id = request.args.get('cliente_id', type=int)
        
    if not cliente_id:
        cliente_id = session.get('cliente_id')
        
    if not cliente_id:
        return redirect(url_for('admin.dashboard'))
        
    cliente_data = AdminModel.buscar_dados_cliente(cliente_id)
    if not cliente_data:
        return redirect(url_for('admin.dashboard'))
        
    layout_config = merge_layout_config(cliente_data.get('layout_config'))
    
    cliente = {
        'id': cliente_data['id'],
        'nome_fantasia': cliente_data['nome_fantasia'],
        'cor_primaria': cliente_data['cor_primaria'],
        'cor_secundaria': cliente_data['cor_secundaria'],
        'cor_terciaria': cliente_data['cor_terciaria'],
        'logo_url': cliente_data['logo_url'],
        'whatsapp': cliente_data['whatsapp'],
        'url_amigavel': cliente_data['url_amigavel'],
        'layout_config': layout_config
    }
    
    return render_template('admin_layout.html', 
                           admin_nome=session['admin_nome'], 
                           cores=cliente, 
                           cliente=cliente)

@admin_bp.route('/api/layout/carregar', methods=['GET'])
def api_carregar_layout():
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
        
    cliente_id = None
    if session.get('tipo') == 'proprietario':
        cliente_id = request.args.get('cliente_id', type=int)
    else:
        permissoes = AdminModel.buscar_permissoes_usuario(session['admin_id'])
        if not permissoes.get('personalizar_aparencia', {}).get('ativo', False):
            return jsonify({'erro': 'Permissão negada'}), 403
            
    if not cliente_id:
        cliente_id = session.get('cliente_id')
        
    if not cliente_id:
        return jsonify({'erro': 'Cliente não encontrado na sessão'}), 404
        
    cliente_data = AdminModel.buscar_dados_cliente(cliente_id)
    if not cliente_data:
        return jsonify({'erro': 'Dados do cliente não encontrados'}), 404
        
    layout_config = merge_layout_config(cliente_data.get('layout_config'))
    
    empresa_id, site_id = AdminModel.buscar_usuario_ids_por_cliente(cliente_id)
    if not empresa_id or not site_id:
        empresa_id = session.get('empresa_id', 1)
        site_id = session.get('site_id', 1)
        
    has_logo = AdminModel.verificar_existe_logo(empresa_id, site_id)
    
    return jsonify({
        'sucesso': True,
        'nome_fantasia': cliente_data['nome_fantasia'],
        'logo_url': cliente_data['logo_url'],
        'whatsapp': cliente_data['whatsapp'],
        'url_amigavel': cliente_data['url_amigavel'],
        'cor_primaria': cliente_data['cor_primaria'],
        'cor_secundaria': cliente_data['cor_secundaria'],
        'cor_terciaria': cliente_data['cor_terciaria'],
        'layout_config': layout_config,
        'has_logo': has_logo,
        'empresa_id': empresa_id,
        'site_id': site_id
    })

@admin_bp.route('/api/layout/salvar', methods=['POST'])
def api_salvar_layout():
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
        
    cliente_id = None
    if session.get('tipo') == 'proprietario':
        cliente_id = request.args.get('cliente_id', type=int)
    else:
        permissoes = AdminModel.buscar_permissoes_usuario(session['admin_id'])
        if not permissoes.get('personalizar_aparencia', {}).get('ativo', False):
            return jsonify({'erro': 'Permissão negada'}), 403
            
    if not cliente_id:
        cliente_id = session.get('cliente_id')
        
    if not cliente_id:
        return jsonify({'erro': 'Cliente não encontrado na sessão'}), 404
        
    dados = request.json
    layout_config_obj = dados.get('layout_config', {})
    
    # Sincronizar dados do cliente na sessão somente se for o próprio cliente do admin logado
    if cliente_id == session.get('cliente_id'):
        session['cliente_nome'] = dados.get('nome_fantasia')
        session['cliente_cor_primaria'] = dados.get('cor_primaria')
        session['cliente_cor_secundaria'] = dados.get('cor_secundaria')
        session['cliente_cor_terciaria'] = dados.get('cor_terciaria')
        session['cliente_logo_url'] = dados.get('logo_url')
        session['cliente_whatsapp'] = dados.get('whatsapp')
        session['cliente_url'] = dados.get('url_amigavel')
    
    update_data = {
        'nome_fantasia': dados.get('nome_fantasia'),
        'cor_primaria': dados.get('cor_primaria'),
        'cor_secundaria': dados.get('cor_secundaria'),
        'cor_terciaria': dados.get('cor_terciaria'),
        'logo_url': dados.get('logo_url'),
        'whatsapp': dados.get('whatsapp'),
        'url_amigavel': dados.get('url_amigavel'),
        'layout_config': json.dumps(layout_config_obj)
    }
    
    resultado = AdminModel.atualizar_cliente(cliente_id, update_data)
    
    return jsonify({
        'sucesso': resultado, 
        'mensagem': 'Aparência e layout salvos com sucesso!' if resultado else 'Erro ao salvar layout'
    })

@admin_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin.login'))

# ==================== ROTAS DE IMOBILIÁRIA E IMAGENS ====================

@admin_bp.route('/imobiliaria/ofertas')
def admin_imobiliaria_ofertas():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    permissoes = AdminModel.buscar_permissoes_usuario(session['admin_id'])
    if not permissoes.get('gerenciar_ofertas', {}).get('ativo', False):
        return redirect(url_for('admin.dashboard'))
        
    cliente = {
        'nome_fantasia': session.get('cliente_nome', session['admin_nome']),
        'cor_primaria': session.get('cliente_cor_primaria', '#667eea'),
        'cor_secundaria': session.get('cliente_cor_secundaria', '#764ba2'),
        'cor_terciaria': session.get('cliente_cor_terciaria', '#48bb78'),
        'logo_url': session.get('cliente_logo_url'),
        'whatsapp': session.get('cliente_whatsapp'),
        'url_amigavel': session.get('cliente_url')
    }
    
    return render_template('admin_imobiliaria.html', 
                           admin_nome=session['admin_nome'], 
                           cores=cliente, 
                           cliente=cliente)

@admin_bp.route('/servicos/imagens')
def admin_servicos_imagens():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))
    
    permissoes = AdminModel.buscar_permissoes_usuario(session['admin_id'])
    if not permissoes.get('imagens_servicos', {}).get('ativo', False):
        return redirect(url_for('admin.dashboard'))
        
    cliente = {
        'nome_fantasia': session.get('cliente_nome', session['admin_nome']),
        'cor_primaria': session.get('cliente_cor_primaria', '#667eea'),
        'cor_secundaria': session.get('cliente_cor_secundaria', '#764ba2'),
        'cor_terciaria': session.get('cliente_cor_terciaria', '#48bb78'),
        'logo_url': session.get('cliente_logo_url'),
        'whatsapp': session.get('cliente_whatsapp'),
        'url_amigavel': session.get('cliente_url')
    }
    
    return render_template('admin_imagens_servico.html', 
                           admin_nome=session['admin_nome'], 
                           cores=cliente, 
                           cliente=cliente)


@admin_bp.route('/api/imobiliaria/ofertas', methods=['GET', 'POST'])
def api_imobiliaria_ofertas():
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
        
    empresa_id = session.get('empresa_id', 1)
    site_id = session.get('site_id', 1)
    
    if request.method == 'GET':
        ofertas = AdminModel.listar_ofertas(empresa_id, site_id)
        # Buscar quais imagens cada oferta tem para o frontend saber o que carregar
        for oferta in ofertas:
            oferta['imagens_ids'] = AdminModel.listar_id_imagens_oferta(oferta['id'])
        return jsonify({'sucesso': True, 'ofertas': ofertas})
        
    elif request.method == 'POST':
        dados = request.json
        oferta_id = dados.get('id')
        dados_json = dados.get('dados', {})
        ativo = dados.get('ativo', True)
        
        novo_id = AdminModel.salvar_oferta(empresa_id, site_id, oferta_id, dados_json, ativo)
        if novo_id:
            return jsonify({'sucesso': True, 'id': novo_id})
        return jsonify({'sucesso': False, 'erro': 'Erro ao salvar oferta'})

@admin_bp.route('/api/imobiliaria/ofertas/<int:oferta_id>', methods=['DELETE'])
def api_excluir_oferta(oferta_id):
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    empresa_id = session.get('empresa_id', 1)
    site_id = session.get('site_id', 1)
    
    resultado = AdminModel.excluir_oferta(empresa_id, site_id, oferta_id)
    return jsonify({'sucesso': resultado})

@admin_bp.route('/api/imobiliaria/ofertas/<int:oferta_id>/imagens', methods=['POST'])
def api_upload_imagens_oferta(oferta_id):
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    
    arquivos_binarios = []
    
    # Process files up to 30
    for i in range(1, 31):
        file_key = f'imagem{i}'
        if file_key in request.files:
            file = request.files[file_key]
            if file and file.filename != '':
                arquivos_binarios.append(file.read())
            else:
                break
        else:
            break
            
    if AdminModel.salvar_imagens_oferta(oferta_id, arquivos_binarios):
        return jsonify({'sucesso': True})
    return jsonify({'sucesso': False, 'erro': 'Erro ao salvar imagens'})

@admin_bp.route('/api/servicos/<int:servico_id>/imagens', methods=['POST'])
def api_upload_imagens_servico(servico_id):
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
        
    empresa_id = session.get('empresa_id', 1)
    site_id = session.get('site_id', 1)
    
    arquivos_binarios = []
    
    # Process files up to 15
    for i in range(1, 16):
        file_key = f'imagem{i}'
        if file_key in request.files:
            file = request.files[file_key]
            if file and file.filename != '':
                arquivos_binarios.append(file.read())
            else:
                break
        else:
            break
            
    if AdminModel.salvar_imagens_servico(empresa_id, site_id, servico_id, arquivos_binarios):
        return jsonify({'sucesso': True})
    return jsonify({'sucesso': False, 'erro': 'Erro ao salvar imagens'})

@admin_bp.route('/api/servicos/<int:servico_id>/imagens/listar', methods=['GET'])
def api_listar_imagens_servico(servico_id):
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    empresa_id = session.get('empresa_id', 1)
    site_id = session.get('site_id', 1)
    
    indices = AdminModel.listar_id_imagens_servico(empresa_id, site_id, servico_id)
    comentarios = AdminModel.buscar_comentarios_imagens_servico(empresa_id, site_id, servico_id)
    return jsonify({'sucesso': True, 'imagens_ids': indices, 'comentarios': comentarios})

@admin_bp.route('/api/servicos/<int:servico_id>/imagens/comentarios', methods=['POST'])
def api_salvar_comentarios_imagens_servico(servico_id):
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    empresa_id = session.get('empresa_id', 1)
    site_id = session.get('site_id', 1)
    comentarios = request.json
    
    resultado = AdminModel.salvar_comentarios_imagens_servico(empresa_id, site_id, servico_id, comentarios)
    return jsonify({'sucesso': resultado})

@admin_bp.route('/api/imobiliaria/ofertas/<int:oferta_id>/imagens/<int:indice_imagem>', methods=['DELETE'])
def api_excluir_imagem_oferta(oferta_id, indice_imagem):
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    resultado = AdminModel.excluir_imagem_oferta(oferta_id, indice_imagem)
    return jsonify({'sucesso': resultado})

@admin_bp.route('/api/servicos/<int:servico_id>/imagens/<int:indice_imagem>', methods=['DELETE'])
def api_excluir_imagem_servico(servico_id, indice_imagem):
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
    empresa_id = session.get('empresa_id', 1)
    site_id = session.get('site_id', 1)
    resultado = AdminModel.excluir_imagem_servico(empresa_id, site_id, servico_id, indice_imagem)
    return jsonify({'sucesso': resultado})

def remover_fundo_branco(img_bytes):
    from PIL import Image
    import io
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        datas = img.getdata()
        
        newData = []
        for item in datas:
            # Se for muito próximo a branco, torna 100% transparente
            if item[0] > 240 and item[1] > 240 and item[2] > 240:
                newData.append((255, 255, 255, 0))
            else:
                newData.append(item)
                
        img.putdata(newData)
        out = io.BytesIO()
        img.save(out, format="PNG")
        return out.getvalue()
    except Exception as e:
        print(f"Erro ao processar imagem para remover fundo: {e}")
        return img_bytes

@admin_bp.route('/api/layout/logo', methods=['POST'])
def api_salvar_logo():
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
        
    cliente_id = None
    if session.get('tipo') == 'proprietario':
        cliente_id = request.form.get('cliente_id', type=int)
    else:
        cliente_id = session.get('cliente_id')
        
    if not cliente_id:
        return jsonify({'erro': 'Cliente não encontrado'}), 400
        
    empresa_id, site_id = AdminModel.buscar_usuario_ids_por_cliente(cliente_id)
    if not empresa_id or not site_id:
        empresa_id = session.get('empresa_id', 1)
        site_id = session.get('site_id', 1)
        
    if 'logo' not in request.files:
        return jsonify({'erro': 'Arquivo não enviado'}), 400
        
    arquivo = request.files['logo']
    if arquivo.filename == '':
        return jsonify({'erro': 'Arquivo vazio'}), 400
        
    try:
        conteudo_binario = arquivo.read()
        # Remover fundo branco
        conteudo_processado = remover_fundo_branco(conteudo_binario)
        
        if AdminModel.salvar_logo(empresa_id, site_id, conteudo_processado):
            return jsonify({'sucesso': True, 'logo_url': f'/img/logo/{empresa_id}/{site_id}'})
        return jsonify({'erro': 'Erro ao salvar no banco de dados'}), 500
    except Exception as e:
        return jsonify({'erro': f'Erro ao processar arquivo: {e}'}), 500

@admin_bp.route('/api/layout/logo', methods=['DELETE'])
def api_excluir_logo():
    if 'admin_id' not in session:
        return jsonify({'erro': 'Não autorizado'}), 401
        
    cliente_id = None
    if session.get('tipo') == 'proprietario':
        cliente_id = request.args.get('cliente_id', type=int)
    else:
        cliente_id = session.get('cliente_id')
        
    if not cliente_id:
        return jsonify({'erro': 'Cliente não encontrado'}), 400
        
    empresa_id, site_id = AdminModel.buscar_usuario_ids_por_cliente(cliente_id)
    if not empresa_id or not site_id:
        empresa_id = session.get('empresa_id', 1)
        site_id = session.get('site_id', 1)
        
    if AdminModel.excluir_logo(empresa_id, site_id):
        return jsonify({'sucesso': True})
    return jsonify({'erro': 'Erro ao excluir do banco de dados'}), 500
