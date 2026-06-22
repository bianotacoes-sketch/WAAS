
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
    return jsonify({'sucesso': True, 'imagens_ids': indices})

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
