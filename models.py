from db_config import get_db_connection
import json
from datetime import datetime, timedelta

class AdminModel:
    @staticmethod
    def autenticar_admin(email, senha):
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT U.ID, U.NOME, U.EMAIL, U.TIPO, U.SENHA, U.EMPRESA_ID, U.SITE_ID, U.CLIENTE_ID,
                   C.NOME_FANTASIA, C.COR_PRIMARIA, C.COR_SECUNDARIA, C.COR_TERCIARIA, C.LOGO_URL, 
                   C.WHATSAPP_NUMERO, C.URL_AMIGAVEL, C.LAYOUT_CONFIG, U.ATIVO
            FROM TESTE.USUARIOS U
            LEFT JOIN TESTE.CLIENTES C ON U.CLIENTE_ID = C.ID
            WHERE U.EMAIL = ?
        """, (email,))
        
        usuario = cursor.fetchone()
        conn.close()
        
        if usuario and senha == usuario[4]:
            ativo = usuario[16] if len(usuario) > 16 and usuario[16] else 'S'
            tipo = usuario[3]
            if tipo != 'proprietario' and ativo == 'N':
                return {'suspenso': True}
                
            return {
                'id': usuario[0],
                'nome': usuario[1],
                'email': usuario[2],
                'tipo': usuario[3],
                'empresa_id': usuario[5] if usuario[5] else 1,
                'site_id': usuario[6] if usuario[6] else 1,
                'cliente_id': usuario[7],
                'cliente_nome': usuario[8] if usuario[8] else usuario[1],
                'cliente_cor_primaria': usuario[9] if usuario[9] else '#667eea',
                'cliente_cor_secundaria': usuario[10] if usuario[10] else '#764ba2',
                'cliente_cor_terciaria': usuario[11] if usuario[11] else '#48bb78',
                'cliente_logo_url': usuario[12],
                'cliente_whatsapp': usuario[13],
                'cliente_url': usuario[14],
                'cliente_layout_config': usuario[15] if len(usuario) > 15 else None
            }
        return None
    
    @staticmethod
    def buscar_permissoes_usuario(usuario_id):
        """Busca as permissões JSON do usuário"""
        conn = get_db_connection()
        if not conn:
            return {}
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT NOME_DASHBOARD, CONFIGURAR_AGENDA, GERENCIAR_SERVICO, PROMOCOES, GERENCIAR_CLIENTES, PERSONALIZAR_APARENCIA,
                   GERENCIAR_OFERTAS, IMAGENS_SERVICOS
            FROM TESTE.USUARIOS 
            WHERE ID = ?
        """, (usuario_id,))
        
        permissoes = cursor.fetchone()
        conn.close()
        
        if permissoes:
            return {
                'nome_dashboard': json.loads(permissoes[0]) if permissoes[0] else {},
                'configurar_agenda': json.loads(permissoes[1]) if permissoes[1] else {},
                'gerenciar_servico': json.loads(permissoes[2]) if permissoes[2] else {},
                'promocoes': json.loads(permissoes[3]) if permissoes[3] else {},
                'gerenciar_clientes': json.loads(permissoes[4]) if permissoes[4] else {},
                'personalizar_aparencia': json.loads(permissoes[5]) if len(permissoes) > 5 and permissoes[5] else {},
                'gerenciar_ofertas': json.loads(permissoes[6]) if len(permissoes) > 6 and permissoes[6] else {},
                'imagens_servicos': json.loads(permissoes[7]) if len(permissoes) > 7 and permissoes[7] else {}
            }
        return {
            'nome_dashboard': {},
            'configurar_agenda': {},
            'gerenciar_servico': {},
            'promocoes': {},
            'gerenciar_clientes': {},
            'personalizar_aparencia': {},
            'gerenciar_ofertas': {},
            'imagens_servicos': {}
        }
    
    @staticmethod
    def atualizar_permissoes_usuario(usuario_id, permissoes):
        """Atualiza as permissões JSON do usuário"""
        conn = get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE TESTE.USUARIOS 
                SET NOME_DASHBOARD = ?,
                    CONFIGURAR_AGENDA = ?,
                    GERENCIAR_SERVICO = ?,
                    PROMOCOES = ?,
                    GERENCIAR_CLIENTES = ?,
                    PERSONALIZAR_APARENCIA = ?,
                    GERENCIAR_OFERTAS = ?,
                    IMAGENS_SERVICOS = ?
                WHERE ID = ?
            """, (
                json.dumps(permissoes.get('nome_dashboard', {})),
                json.dumps(permissoes.get('configurar_agenda', {})),
                json.dumps(permissoes.get('gerenciar_servico', {})),
                json.dumps(permissoes.get('promocoes', {})),
                json.dumps(permissoes.get('gerenciar_clientes', {})),
                json.dumps(permissoes.get('personalizar_aparencia', {})),
                json.dumps(permissoes.get('gerenciar_ofertas', {})),
                json.dumps(permissoes.get('imagens_servicos', {})),
                usuario_id
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao atualizar permissões: {e}")
            conn.close()
            return False
    
    @staticmethod
    def buscar_dados_cliente(cliente_id):
        """Busca dados de personalização do cliente"""
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID, NOME_FANTASIA, URL_AMIGAVEL, COR_PRIMARIA, COR_SECUNDARIA, 
                   COR_TERCIARIA, LOGO_URL, WHATSAPP_NUMERO, ATIVO, LAYOUT_CONFIG
            FROM TESTE.CLIENTES 
            WHERE ID = ?
        """, (cliente_id,))
        
        cliente = cursor.fetchone()
        conn.close()
        
        if cliente:
            return {
                'id': cliente[0],
                'nome_fantasia': cliente[1],
                'url_amigavel': cliente[2],
                'cor_primaria': cliente[3] if cliente[3] else '#667eea',
                'cor_secundaria': cliente[4] if cliente[4] else '#764ba2',
                'cor_terciaria': cliente[5] if cliente[5] else '#48bb78',
                'logo_url': cliente[6],
                'whatsapp': cliente[7],
                'ativo': cliente[8],
                'layout_config': cliente[9] if len(cliente) > 9 else None
            }
        return None
    
    @staticmethod
    def listar_clientes():
        """Lista todos os clientes para o proprietário"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT C.ID, C.NOME_FANTASIA, C.URL_AMIGAVEL, C.COR_PRIMARIA, C.COR_SECUNDARIA, 
                   C.COR_TERCIARIA, C.LOGO_URL, C.WHATSAPP_NUMERO, C.ATIVO,
                   U.NOME as USUARIO_NOME, U.EMAIL as USUARIO_EMAIL, C.LAYOUT_CONFIG
            FROM TESTE.CLIENTES C
            JOIN TESTE.USUARIOS U ON C.USUARIO_ID = U.ID
            ORDER BY C.ID
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
                'layout_config': row[11] if len(row) > 11 else None
            })
        conn.close()
        return clientes
    
    @staticmethod
    def atualizar_cliente(cliente_id, dados):
        """Atualiza os dados de personalização do cliente"""
        conn = get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            if 'layout_config' in dados:
                cursor.execute("""
                    UPDATE TESTE.CLIENTES 
                    SET NOME_FANTASIA = ?,
                        COR_PRIMARIA = ?,
                        COR_SECUNDARIA = ?,
                        COR_TERCIARIA = ?,
                        LOGO_URL = ?,
                        WHATSAPP_NUMERO = ?,
                        URL_AMIGAVEL = ?,
                        LAYOUT_CONFIG = ?
                    WHERE ID = ?
                """, (
                    dados.get('nome_fantasia'),
                    dados.get('cor_primaria', '#667eea'),
                    dados.get('cor_secundaria', '#764ba2'),
                    dados.get('cor_terciaria', '#48bb78'),
                    dados.get('logo_url'),
                    dados.get('whatsapp'),
                    dados.get('url_amigavel'),
                    dados.get('layout_config'),
                    cliente_id
                ))
            else:
                cursor.execute("""
                    UPDATE TESTE.CLIENTES 
                    SET NOME_FANTASIA = ?,
                        COR_PRIMARIA = ?,
                        COR_SECUNDARIA = ?,
                        COR_TERCIARIA = ?,
                        LOGO_URL = ?,
                        WHATSAPP_NUMERO = ?,
                        URL_AMIGAVEL = ?
                    WHERE ID = ?
                """, (
                    dados.get('nome_fantasia'),
                    dados.get('cor_primaria', '#667eea'),
                    dados.get('cor_secundaria', '#764ba2'),
                    dados.get('cor_terciaria', '#48bb78'),
                    dados.get('logo_url'),
                    dados.get('whatsapp'),
                    dados.get('url_amigavel'),
                    cliente_id
                ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao atualizar cliente: {e}")
            conn.close()
            return False

    @staticmethod
    def carregar_servicos(empresa_id, site_id):
        conn = get_db_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, SERVICO FROM TESTE.SERVICOS 
                WHERE empresa_id = ? AND site_id = ?
                ORDER BY id
            """, (empresa_id, site_id))
            resultados = cursor.fetchall()
            
            img_cursor = conn.cursor()
            servicos = []
            for row in resultados:
                db_id = row[0]
                if row[1]:
                    servico_obj = json.loads(row[1]) if isinstance(row[1], str) else row[1]
                    if isinstance(servico_obj, dict):
                        servico_obj['id'] = db_id
                        
                        # Obter índices de imagens e comentários sem carregar os BLOBs
                        cols = ", ".join([f"CASE WHEN imagem{i} IS NOT NULL THEN 1 ELSE 0 END" for i in range(1, 16)])
                        img_cursor.execute(f"SELECT {cols}, comentarios FROM teste.imagens WHERE empresa_id = ? AND site_id = ? AND servico_id = ?", (empresa_id, site_id, db_id))
                        img_row = img_cursor.fetchone()
                        indices = []
                        comentarios = {}
                        if img_row:
                            for idx in range(15):
                                if img_row[idx] == 1:
                                    indices.append(idx + 1)
                            comentarios_val = img_row[15]
                            if comentarios_val:
                                try:
                                    comentarios = json.loads(comentarios_val) if isinstance(comentarios_val, str) else comentarios_val
                                except Exception as e:
                                    print(f"Erro ao parsear comentarios no servico {db_id}: {e}")
                        servico_obj['imagens_ids'] = indices
                        servico_obj['imagens_comentarios'] = comentarios
                    servicos.append(servico_obj)
            conn.close()
            return servicos
        except Exception as e:
            print(f"Erro ao carregar serviços: {e}")
            if 'conn' in locals(): conn.close()
            return []
    
    @staticmethod
    def adicionar_servico(empresa_id, site_id, servico):
        conn = get_db_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            servico_json = json.dumps(servico)
            cursor.execute("""
                INSERT INTO TESTE.SERVICOS (empresa_id, site_id, SERVICO)
                VALUES (?, ?, ?)
            """, (empresa_id, site_id, servico_json))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao adicionar serviço: {e}")
            conn.close()
            return False
    
    @staticmethod
    def editar_servico(empresa_id, site_id, index, servico):
        conn = get_db_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, SERVICO FROM TESTE.SERVICOS 
                WHERE empresa_id = ? AND site_id = ?
                ORDER BY id
            """, (empresa_id, site_id))
            resultados = cursor.fetchall()
            if index < len(resultados):
                servico_id = resultados[index][0]
                servico_json = json.dumps(servico)
                cursor.execute("""
                    UPDATE TESTE.SERVICOS 
                    SET SERVICO = ?
                    WHERE id = ?
                """, (servico_json, servico_id))
                conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao editar serviço: {e}")
            conn.close()
            return False
    
    @staticmethod
    def excluir_servico(empresa_id, site_id, index):
        conn = get_db_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM TESTE.SERVICOS 
                WHERE empresa_id = ? AND site_id = ?
                ORDER BY id
            """, (empresa_id, site_id))
            resultados = cursor.fetchall()
            if index < len(resultados):
                servico_id = resultados[index][0]
                cursor.execute("DELETE FROM TESTE.SERVICOS WHERE id = ?", (servico_id,))
                conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao excluir serviço: {e}")
            conn.close()
            return False
    
    @staticmethod
    def carregar_cronograma_semanal(data_inicio):
        conn = get_db_connection()
        if not conn:
            return {}
        try:
            data_fim = datetime.strptime(data_inicio, '%Y-%m-%d') + timedelta(days=7)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DATA, CRONOGRAMA 
                FROM TESTE.AGENDA 
                WHERE DATA >= ? AND DATA < ?
                ORDER BY DATA
            """, (data_inicio, data_fim.strftime('%Y-%m-%d')))
            resultados = cursor.fetchall()
            conn.close()
            cronograma = {}
            for row in resultados:
                data = row[0].strftime('%Y-%m-%d')
                if row[1]:
                    cronograma[data] = json.loads(row[1])
                else:
                    cronograma[data] = {}
            return cronograma
        except Exception as e:
            print(f"Erro ao carregar cronograma: {e}")
            return {}
    
    @staticmethod
    def salvar_cronograma_semanal(data_inicio, config_semana):
        conn = get_db_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            for data_str, config in config_semana['dias'].items():
                cursor.execute("SELECT COUNT(*) FROM TESTE.AGENDA WHERE DATA = ?", (data_str,))
                existe = cursor.fetchone()[0] > 0
                cronograma_json = json.dumps(config)
                if existe:
                    cursor.execute("UPDATE TESTE.AGENDA SET CRONOGRAMA = ? WHERE DATA = ?", (cronograma_json, data_str))
                else:
                    cursor.execute("INSERT INTO TESTE.AGENDA (DATA, CRONOGRAMA) VALUES (?, ?)", (data_str, cronograma_json))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao salvar cronograma: {e}")
            conn.close()
            return False

    @staticmethod
    def listar_promocoes(empresa_id, site_id, apenas_ativas=False):
        conn = get_db_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT id, nome_promocao, data_promocao, data_fim, ativa, detalhes
                FROM TESTE.PROMOCOES
                WHERE empresa_id = ? AND site_id = ?
            """
            params = [empresa_id, site_id]
            if apenas_ativas:
                query += " AND ativa = 'S'"
                query += " AND (data_fim IS NULL OR data_fim >= CAST(GETDATE() AS DATE))"
            query += " ORDER BY data_promocao DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            promos = []
            for row in rows:
                promos.append({
                    'id': row[0],
                    'nome': row[1],
                    'data_inicio': row[2].strftime('%Y-%m-%d') if row[2] else None,
                    'data_fim': row[3].strftime('%Y-%m-%d') if row[3] else None,
                    'ativa': row[4],
                    'detalhes': json.loads(row[5]) if row[5] else {}
                })
            return promos
        except Exception as e:
            print(f"Erro ao listar promoções: {e}")
            return []
    
    @staticmethod
    def salvar_promocao(empresa_id, site_id, dados):
        conn = get_db_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            promo_id = dados.get('id')
            nome = dados.get('nome')
            data_inicio = dados.get('data_inicio')
            data_fim = dados.get('data_fim') if dados.get('data_fim') else None
            ativa = 'S' if dados.get('ativa') else 'N'
            detalhes = json.dumps(dados.get('detalhes', {}))
            if promo_id:
                cursor.execute("""
                    UPDATE TESTE.PROMOCOES
                    SET nome_promocao = ?,
                        data_promocao = ?,
                        data_fim = ?,
                        ativa = ?,
                        detalhes = ?
                    WHERE id = ? AND empresa_id = ? AND site_id = ?
                """, (nome, data_inicio, data_fim, ativa, detalhes, promo_id, empresa_id, site_id))
            else:
                cursor.execute("""
                    INSERT INTO TESTE.PROMOCOES (empresa_id, site_id, nome_promocao, data_promocao, data_fim, ativa, detalhes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (empresa_id, site_id, nome, data_inicio, data_fim, ativa, detalhes))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao salvar promoção: {e}")
            conn.close()
            return False
    
    @staticmethod
    def excluir_promocao(empresa_id, site_id, promo_id):
        conn = get_db_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM TESTE.PROMOCOES WHERE id = ? AND empresa_id = ? AND site_id = ?", (promo_id, empresa_id, site_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao excluir promoção: {e}")
            conn.close()
            return False
    
    @staticmethod
    def alternar_ativa_promocao(empresa_id, site_id, promo_id, ativa):
        conn = get_db_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            ativa_char = 'S' if ativa else 'N'
            cursor.execute("UPDATE TESTE.PROMOCOES SET ativa = ? WHERE id = ? AND empresa_id = ? AND site_id = ?", (ativa_char, promo_id, empresa_id, site_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao alternar status da promoção: {e}")
            conn.close()
            return False
    @staticmethod
    def listar_ofertas(empresa_id, site_id):
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, ofertas, ativo FROM teste.imobiliaria WHERE empresa_id = ? AND site_id = ?", (empresa_id, site_id))
            resultados = cursor.fetchall()
            conn.close()
            ofertas = []
            for row in resultados:
                ofertas.append({
                    'id': row[0],
                    'dados': json.loads(row[1]) if row[1] else {},
                    'ativo': row[2] == 'S'
                })
            return ofertas
        except Exception as e:
            print(f"Erro ao listar ofertas: {e}")
            if 'conn' in locals(): conn.close()
            return []

    @staticmethod
    def salvar_oferta(empresa_id, site_id, oferta_id, dados_json, ativo):
        conn = get_db_connection()
        if not conn: return None
        try:
            cursor = conn.cursor()
            ativo_str = 'S' if ativo else 'N'
            if oferta_id:
                cursor.execute("""
                    UPDATE teste.imobiliaria SET ofertas = ?, ativo = ? 
                    WHERE id = ? AND empresa_id = ? AND site_id = ?
                """, (json.dumps(dados_json), ativo_str, oferta_id, empresa_id, site_id))
            else:
                cursor.execute("""
                    INSERT INTO teste.imobiliaria (site_id, empresa_id, ofertas, ativo, data_criacao)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, GETDATE())
                """, (site_id, empresa_id, json.dumps(dados_json), ativo_str))
                oferta_id = cursor.fetchone()[0]
            conn.commit()
            conn.close()
            return oferta_id
        except Exception as e:
            print(f"Erro ao salvar oferta: {e}")
            if 'conn' in locals(): conn.close()
            return None

    @staticmethod
    def excluir_oferta(empresa_id, site_id, oferta_id):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            # Delete associated images first
            cursor.execute("DELETE FROM teste.imobiliaria_imagens WHERE oferta_id = ?", (oferta_id,))
            # Delete offer
            cursor.execute("DELETE FROM teste.imobiliaria WHERE id = ? AND empresa_id = ? AND site_id = ?", (oferta_id, empresa_id, site_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao excluir oferta: {e}")
            if 'conn' in locals(): conn.close()
            return False

    @staticmethod
    def salvar_imagens_oferta(oferta_id, imagens_binarias):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM teste.imobiliaria_imagens WHERE oferta_id = ?", (oferta_id,))
            existe = cursor.fetchone()
            
            # Limit to 30 images total
            imagens_binarias = imagens_binarias[:30]
            
            if len(imagens_binarias) > 0:
                if not existe:
                    colunas = [f"imagem{i+1}" for i in range(len(imagens_binarias))]
                    cols_str = ", ".join(colunas)
                    vals_str = ", ".join(["?" for _ in colunas])
                    params = [oferta_id] + imagens_binarias
                    cursor.execute(f"INSERT INTO teste.imobiliaria_imagens (oferta_id, {cols_str}) VALUES (?, {vals_str})", params)
                else:
                    # Encontrar quais colunas estão vazias (NULL)
                    cols_check = ", ".join([f"CASE WHEN imagem{i} IS NULL THEN 1 ELSE 0 END" for i in range(1, 31)])
                    cursor.execute(f"SELECT {cols_check} FROM teste.imobiliaria_imagens WHERE oferta_id = ?", (oferta_id,))
                    null_row = cursor.fetchone()
                    
                    if null_row:
                        null_indices = [idx + 1 for idx, is_null in enumerate(null_row) if is_null == 1]
                        
                        updates = []
                        params = []
                        for idx, img_bin in enumerate(imagens_binarias):
                            if idx < len(null_indices):
                                target_col = f"imagem{null_indices[idx]}"
                                updates.append(f"{target_col} = ?")
                                params.append(img_bin)
                        
                        if updates:
                            params.append(oferta_id)
                            set_clause = ", ".join(updates)
                            cursor.execute(f"UPDATE teste.imobiliaria_imagens SET {set_clause} WHERE oferta_id = ?", params)
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao salvar imagens da oferta: {e}")
            if 'conn' in locals(): conn.close()
            return False

    @staticmethod
    def listar_id_imagens_oferta(oferta_id):
        # Retorna apenas quais índices (1 a 30) têm imagem salva para não trafegar o BLOB inteiro
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cols = ", ".join([f"CASE WHEN imagem{i} IS NOT NULL THEN 1 ELSE 0 END" for i in range(1, 31)])
            cursor.execute(f"SELECT {cols} FROM teste.imobiliaria_imagens WHERE oferta_id = ?", (oferta_id,))
            row = cursor.fetchone()
            conn.close()
            if not row: return []
            
            indices = []
            for idx, has_img in enumerate(row):
                if has_img == 1:
                    indices.append(idx + 1)
            return indices
        except Exception as e:
            print(f"Erro ao listar índices de imagens: {e}")
            if 'conn' in locals(): conn.close()
            return []

    @staticmethod
    def buscar_imagem_oferta(oferta_id, indice_imagem):
        if indice_imagem < 1 or indice_imagem > 30: return None
        conn = get_db_connection()
        if not conn: return None
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT imagem{indice_imagem} FROM teste.imobiliaria_imagens WHERE oferta_id = ?", (oferta_id,))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            print(f"Erro ao buscar imagem: {e}")
            if 'conn' in locals(): conn.close()
            return None

    @staticmethod
    def excluir_imagem_oferta(oferta_id, indice_imagem):
        if indice_imagem < 1 or indice_imagem > 30: return False
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE teste.imobiliaria_imagens SET imagem{indice_imagem} = NULL WHERE oferta_id = ?", (oferta_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao excluir imagem da oferta: {e}")
            if 'conn' in locals(): conn.close()
            return False

    @staticmethod
    def salvar_imagens_servico(empresa_id, site_id, servico_id, imagens_binarias):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM teste.imagens WHERE empresa_id = ? AND site_id = ? AND servico_id = ?", (empresa_id, site_id, servico_id))
            existe = cursor.fetchone()
            
            # Limit to 15 images total
            imagens_binarias = imagens_binarias[:15]
            
            if len(imagens_binarias) > 0:
                if not existe:
                    colunas = [f"imagem{i+1}" for i in range(len(imagens_binarias))]
                    cols_str = ", ".join(colunas)
                    vals_str = ", ".join(["?" for _ in colunas])
                    params = [empresa_id, site_id, servico_id] + imagens_binarias
                    cursor.execute(f"INSERT INTO teste.imagens (empresa_id, site_id, servico_id, {cols_str}) VALUES (?, ?, ?, {vals_str})", params)
                else:
                    # Encontrar quais colunas estão vazias (NULL)
                    cols_check = ", ".join([f"CASE WHEN imagem{i} IS NULL THEN 1 ELSE 0 END" for i in range(1, 16)])
                    cursor.execute(f"SELECT {cols_check} FROM teste.imagens WHERE empresa_id = ? AND site_id = ? AND servico_id = ?", (empresa_id, site_id, servico_id))
                    null_row = cursor.fetchone()
                    
                    if null_row:
                        null_indices = [idx + 1 for idx, is_null in enumerate(null_row) if is_null == 1]
                        
                        updates = []
                        params = []
                        for idx, img_bin in enumerate(imagens_binarias):
                            if idx < len(null_indices):
                                target_col = f"imagem{null_indices[idx]}"
                                updates.append(f"{target_col} = ?")
                                params.append(img_bin)
                        
                        if updates:
                            params.extend([empresa_id, site_id, servico_id])
                            set_clause = ", ".join(updates)
                            cursor.execute(f"UPDATE teste.imagens SET {set_clause} WHERE empresa_id = ? AND site_id = ? AND servico_id = ?", params)
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao salvar imagens servico: {e}")
            if 'conn' in locals(): conn.close()
            return False

    @staticmethod
    def listar_id_imagens_servico(empresa_id, site_id, servico_id):
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cols = ", ".join([f"CASE WHEN imagem{i} IS NOT NULL THEN 1 ELSE 0 END" for i in range(1, 16)])
            cursor.execute(f"SELECT {cols} FROM teste.imagens WHERE empresa_id = ? AND site_id = ? AND servico_id = ?", (empresa_id, site_id, servico_id))
            row = cursor.fetchone()
            conn.close()
            if not row: return []
            
            indices = []
            for idx, has_img in enumerate(row):
                if has_img == 1:
                    indices.append(idx + 1)
            return indices
        except Exception as e:
            print(f"Erro ao listar imagens servico: {e}")
            if 'conn' in locals(): conn.close()
            return []

    @staticmethod
    def buscar_imagem_servico(empresa_id, site_id, servico_id, indice_imagem):
        if indice_imagem < 1 or indice_imagem > 15: return None
        conn = get_db_connection()
        if not conn: return None
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT imagem{indice_imagem} FROM teste.imagens WHERE empresa_id = ? AND site_id = ? AND servico_id = ?", (empresa_id, site_id, servico_id))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            print(f"Erro ao buscar imagem servico: {e}")
            if 'conn' in locals(): conn.close()
            return None

    @staticmethod
    def excluir_imagem_servico(empresa_id, site_id, servico_id, indice_imagem):
        if indice_imagem < 1 or indice_imagem > 15: return False
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE teste.imagens SET imagem{indice_imagem} = NULL WHERE empresa_id = ? AND site_id = ? AND servico_id = ?", (empresa_id, site_id, servico_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao excluir imagem do servico: {e}")
            if 'conn' in locals(): conn.close()
            return False

    @staticmethod
    def buscar_comentarios_imagens_servico(empresa_id, site_id, servico_id):
        conn = get_db_connection()
        if not conn:
            return {}
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT comentarios FROM teste.imagens WHERE empresa_id = ? AND site_id = ? AND servico_id = ?", (empresa_id, site_id, servico_id))
            row = cursor.fetchone()
            conn.close()
            if row and row[0]:
                return json.loads(row[0]) if isinstance(row[0], str) else row[0]
            return {}
        except Exception as e:
            print(f"Erro ao buscar comentarios imagens servico: {e}")
            if 'conn' in locals(): conn.close()
            return {}

    @staticmethod
    def salvar_comentarios_imagens_servico(empresa_id, site_id, servico_id, comentarios):
        conn = get_db_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM teste.imagens WHERE empresa_id = ? AND site_id = ? AND servico_id = ?", (empresa_id, site_id, servico_id))
            existe = cursor.fetchone()
            comentarios_json = json.dumps(comentarios)
            if existe:
                cursor.execute("UPDATE teste.imagens SET comentarios = ? WHERE empresa_id = ? AND site_id = ? AND servico_id = ?", (comentarios_json, empresa_id, site_id, servico_id))
            else:
                cursor.execute("INSERT INTO teste.imagens (empresa_id, site_id, servico_id, comentarios) VALUES (?, ?, ?, ?)", (empresa_id, site_id, servico_id, comentarios_json))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao salvar comentarios imagens servico: {e}")
            if 'conn' in locals(): conn.close()
            return False

    @staticmethod
    def buscar_logo(empresa_id, site_id):
        conn = get_db_connection()
        if not conn: return None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT logo FROM teste.logo WHERE empresa_id = ? AND site_id = ?", (empresa_id, site_id))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            print(f"Erro ao buscar logo: {e}")
            if 'conn' in locals(): conn.close()
            return None

    @staticmethod
    def verificar_existe_logo(empresa_id, site_id):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM teste.logo WHERE empresa_id = ? AND site_id = ?", (empresa_id, site_id))
            existe = cursor.fetchone()[0] > 0
            conn.close()
            return existe
        except Exception as e:
            print(f"Erro ao verificar logo: {e}")
            if 'conn' in locals(): conn.close()
            return False

    @staticmethod
    def salvar_logo(empresa_id, site_id, logo_binario):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM teste.logo WHERE empresa_id = ? AND site_id = ?", (empresa_id, site_id))
            existe = cursor.fetchone()
            if existe:
                cursor.execute("UPDATE teste.logo SET logo = ? WHERE empresa_id = ? AND site_id = ?", (logo_binario, empresa_id, site_id))
            else:
                cursor.execute("INSERT INTO teste.logo (empresa_id, site_id, logo) VALUES (?, ?, ?)", (empresa_id, site_id, logo_binario))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao salvar logo: {e}")
            if 'conn' in locals(): conn.close()
            return False

    @staticmethod
    def excluir_logo(empresa_id, site_id):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM teste.logo WHERE empresa_id = ? AND site_id = ?", (empresa_id, site_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao excluir logo: {e}")
            if 'conn' in locals(): conn.close()
            return False

    @staticmethod
    def buscar_usuario_ids_por_cliente(cliente_id):
        conn = get_db_connection()
        if not conn: return None, None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT U.EMPRESA_ID, U.SITE_ID 
                FROM TESTE.USUARIOS U 
                JOIN TESTE.CLIENTES C ON C.USUARIO_ID = U.ID 
                WHERE C.ID = ?
            """, (cliente_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return row[0], row[1]
            return None, None
        except Exception as e:
            print(f"Erro ao buscar ids do usuario por cliente: {e}")
            if 'conn' in locals(): conn.close()
            return None, None
