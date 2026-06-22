import PyPDF2
import pandas as pd
import re
import unicodedata
import pyodbc
import os
import zipfile
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO


# Função para normalizar texto (remover acentos e converter para maiúsculas)
def normalizar_texto(texto):
    texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII")
    return texto.upper()


# Função para extrair texto de uma página do PDF
def extrair_texto_pagina(pdf_reader, numero_pagina):
    pagina = pdf_reader.pages[numero_pagina]
    return pagina.extract_text()


# Função para extrair os dois primeiros nomes do beneficiário
def extrair_dois_primeiros_nomes(beneficiario):
    nomes = beneficiario.split()
    if len(nomes) >= 2:
        return "".join(nomes[:2])
    return beneficiario.replace(" ", "")


# Função para limpar CPF (remove pontos, traços e espaços)
def limpar_cpf(cpf):
    if cpf:
        return re.sub(r'[^\d]', '', str(cpf))
    return ''


# Função para limpar conta (remove zeros à esquerda)
def limpar_conta(conta):
    if conta:
        conta_limpa = str(conta).lstrip('0')
        return conta_limpa if conta_limpa else '0'
    return ''


# ==================== FUNÇÕES PARA BANCO DE DADOS ====================
def buscar_dados_no_banco():
    """Conecta ao banco Sankhya e busca os dados com chave_matricula e CPF"""
   
    server = "134.65.243.58,1433"
    database = "SANKHYA_PROD"
    username = "sankhya"
    password = "h4xg7s3f"
   
    conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"

    try:
        conn = pyodbc.connect(conn_str, timeout=30)
        cursor = conn.cursor()
       
        query = """
        SELECT
            REPLACE(CONCAT(LEFT(codage, 4), codctabco), ' ', '') AS chave_matricula,
            matricula,
            codage,
            codctabco,
            cpf
        FROM TFPFUN
        WHERE codage IS NOT NULL AND codctabco IS NOT NULL
        """
       
        cursor.execute(query)
        dados_banco = cursor.fetchall()
       
        df_banco = pd.DataFrame.from_records(
            dados_banco,
            columns=["chave_matricula", "matricula", "codage", "codctabco", "cpf"]
        )
       
        df_banco['cpf_limpo'] = df_banco['cpf'].astype(str).apply(limpar_cpf)
       
        cursor.close()
        conn.close()
       
        print(f"  ✅ Banco: {len(df_banco)} registros")
        if not df_banco.empty:
            print(f"  📊 Exemplo CPF: {df_banco['cpf_limpo'].iloc[0]}")
            print(f"  📊 Exemplo chave_matricula: {df_banco['chave_matricula'].iloc[0]}")
        return df_banco
       
    except Exception as e:
        print(f"  ❌ Erro banco: {e}")
        return pd.DataFrame()


# ==================== FUNÇÕES PARA COMPROVANTE ====================
def extrair_dados_comprovante(texto_normalizado):
    """Tenta extrair dados do comprovante usando múltiplos padrões de regex"""
   
    # ===== PADRÕES PARA BENEFICIÁRIO =====
    padroes_beneficiario = [
        r"FAVORECIDO:?\s*(.+)",
        r"CLIENTE:?\s*(.+)",
        r"BENEFICIARIO:?\s*(.+)",
        r"PAGO PARA:?\s*(.+)",
        r"NOME:?\s*(.+)",
    ]
   
    # ===== PADRÕES PARA CPF =====
    padroes_cpf = [
        r"FAVORECIDO:?\s*.+?\s*(\d{3}\.\d{3}\.\d{3}-\d{2})",
        r"CPF:?\s*(\d{3}\.\d{3}\.\d{3}-\d{2})",
        r"CPF:?\s*(\d{11})",
        r"(\d{3}\.\d{3}\.\d{3}-\d{2})",
    ]
   
    # ===== PADRÕES PARA VALOR =====
    padroes_valor = [
        r"VALOR\s*\(R\$\):?\s*\d{2}/\d{2}/\d{4}\s*([\d.,]+)",
        r"VALOR\s*\(R\$\):?\s*([\d.,]+)",
        r"VALOR\s*(?:TOTAL)?\s*R?\$?\s*([\d.,]+)",
        r"VALOR\s*R?\$?\s*([\d.,]+)",
        r"R?\$?\s*([\d.,]+)\s*$",
    ]
   
    # ===== PADRÕES PARA AGÊNCIA =====
    padroes_agencia = [
        r"AGENCIA:?\s*(\d+)\s*[|\-]",  # Agência: 36064 |
        r"AGENCIA:?\s*(\d+)",
        r"AG[EÊ]NCIA:?\s*(\d+)",
    ]
   
    # ===== PADRÕES PARA CONTA =====
    padroes_conta = [
        r"CONTA:?\s*(\d+)",  # Conta: 20001
        r"CONTA\s*:?\s*(\d+\s*[-\/]?\s*\d*)",
        r"CONTA\s*CORRENTE:?\s*(\d+)",
    ]
   
    # Tenta cada padrão de beneficiário
    beneficiario = None
    for padrao in padroes_beneficiario:
        match = re.search(padrao, texto_normalizado)
        if match:
            beneficiario = match
            break
   
    # Tenta cada padrão de CPF
    cpf_match = None
    for padrao in padroes_cpf:
        match = re.search(padrao, texto_normalizado)
        if match:
            cpf_match = match
            break
   
    # Tenta cada padrão de valor
    valor = None
    for padrao in padroes_valor:
        match = re.search(padrao, texto_normalizado)
        if match:
            valor = match
            break
   
    # ===== EXTRAÇÃO ESPECIAL PARA AGÊNCIA E CONTA =====
    # Primeiro, tenta encontrar o padrão "8906 Conta:332633" no final
    padrao_final = re.search(r"(\d{4})\s+CONTA:?\s*(\d+)", texto_normalizado)
    if padrao_final:
        agencia_funcionario = padrao_final.group(1)
        conta_funcionario = limpar_conta(padrao_final.group(2))
    else:
        # Tenta encontrar "8906 332633" (agencia + conta sem "CONTA:")
        padrao_final = re.search(r"(\d{4})\s+(\d{6})", texto_normalizado)
        if padrao_final:
            agencia_funcionario = padrao_final.group(1)
            conta_funcionario = limpar_conta(padrao_final.group(2))
        else:
            agencia_funcionario = None
            conta_funcionario = None
   
    # Se não encontrou no final, usa os métodos tradicionais
    if agencia_funcionario is None:
        # Tenta padrões normais de agência
        agencias = []
        for padrao in padroes_agencia:
            matches = re.findall(padrao, texto_normalizado)
            if matches:
                agencias = matches
                break
       
        # Tenta padrões normais de conta
        contas = []
        for padrao in padroes_conta:
            matches = re.findall(padrao, texto_normalizado)
            if matches:
                contas = [limpar_conta(m) for m in matches]
                break
       
        # Caso especial: "Agência: 36064 | Conta: 20001"
        if len(agencias) < 2:
            match_remetente = re.search(r"AGENCIA:?\s*(\d+)\s*[|\-]\s*CONTA:?\s*(\d+)", texto_normalizado)
            if match_remetente:
                agencias.insert(0, match_remetente.group(1))
                contas.insert(0, limpar_conta(match_remetente.group(2)))
       
        # Caso especial: "AGENCIA: CONTA 94390 3875"
        if len(agencias) < 2:
            match_remetente = re.search(r"AGENCIA:\s*CONTA\s*(\d+)\s*(\d+)", texto_normalizado)
            if match_remetente:
                agencias.insert(0, match_remetente.group(1))
                contas.insert(0, limpar_conta(match_remetente.group(2)))
       
        # Se encontrou pelo menos 2 agências e contas, pega a última
        if len(agencias) >= 2 and len(contas) >= 2:
            agencia_funcionario = agencias[-1]
            conta_funcionario = contas[-1]
        else:
            agencia_funcionario = None
            conta_funcionario = None
   
    return beneficiario, cpf_match, valor, agencia_funcionario, conta_funcionario


def processar_pdf_principal(caminho_pdf):
    """Processa o PDF principal (comprovante)"""
   
    with open(caminho_pdf, "rb") as arquivo_pdf:
        pdf_reader = PyPDF2.PdfReader(arquivo_pdf)
        num_paginas = len(pdf_reader.pages)
        dados = []
       
        print(f"\n📄 Comprovante: {num_paginas} páginas")
       
        # Pega a primeira página para debug
        if num_paginas > 0:
            print("\n" + "="*60)
            print("📄 PRIMEIRA PÁGINA DO COMPROVANTE:")
            print("="*60)
            texto_primeira = extrair_texto_pagina(pdf_reader, 0)
            print(texto_primeira[:1500])
            print("="*60)
            print()
       
        for numero_pagina in range(num_paginas):
            texto = extrair_texto_pagina(pdf_reader, numero_pagina)
            texto_normalizado = normalizar_texto(texto)
           
            beneficiario, cpf_match, valor, agencia_funcionario, conta_funcionario = extrair_dados_comprovante(texto_normalizado)
           
            # DEBUG: Mostra o que foi encontrado na primeira página
            if numero_pagina == 0:
                print("🔍 DEBUG - Primeira página:")
                print(f"   Beneficiário: {beneficiario.group(1).strip() if beneficiario else 'NÃO ENCONTRADO'}")
                print(f"   CPF: {cpf_match.group(1).strip() if cpf_match else 'NÃO ENCONTRADO'}")
                print(f"   Valor: {valor.group(1).strip() if valor else 'NÃO ENCONTRADO'}")
                print(f"   Agência Funcionário: {agencia_funcionario}")
                print(f"   Conta Funcionário: {conta_funcionario}")
                print()
           
            if beneficiario and valor and agencia_funcionario and conta_funcionario:
                # Extrai CPF se encontrou
                cpf = limpar_cpf(cpf_match.group(1).strip() if cpf_match else '')
               
                dois_primeiros_nomes = extrair_dois_primeiros_nomes(beneficiario.group(1).strip())
               
                valor_bruto = valor.group(1).strip()
                valor_limpo = re.sub(r'[^\d]', '', valor_bruto)
               
                chave1 = f"{dois_primeiros_nomes}{valor_limpo}"
                chave_matricula = f"{agencia_funcionario}{conta_funcionario}"
               
                dados.append({
                    "Beneficiário": beneficiario.group(1).strip(),
                    "CPF": cpf,
                    "Valor": valor_bruto,
                    "Valor_Limpo": valor_limpo,
                    "Agência": agencia_funcionario,
                    "Conta": conta_funcionario,
                    "Página": numero_pagina + 1,
                    "chave1": chave1,
                    "chave_matricula": chave_matricula
                })
       
        df = pd.DataFrame(dados)
        print(f"✅ Comprovante: {len(df)} registros extraídos")
       
        if df.empty:
            print("⚠️ NENHUM dado extraído do comprovante!")
            return df
       
        print("\n📊 DF_COMPROVANTE (primeiros 5):")
        print(df[['Beneficiário', 'CPF', 'Valor', 'Agência', 'Conta', 'chave_matricula']].head())
        print(f"   Total: {len(df)} registros")
       
        # ===== NOVA ESTRATÉGIA: Buscar CPFs no banco usando chave_matricula =====
        print("\n🔍 Buscando CPFs no banco usando chave_matricula...")
        df_banco = buscar_dados_no_banco()
       
        if not df_banco.empty:
            # Faz o merge para encontrar o CPF de cada funcionário
            df = pd.merge(df, df_banco[['chave_matricula', 'cpf_limpo', 'matricula']], 
                         on="chave_matricula", how="left")
            
            # Se encontrou CPF, usa ele; senão mantém o CPF que já tinha (se houver)
            df['CPF_encontrado'] = df['cpf_limpo'].fillna(df['CPF'])
            
            encontrou_cpf = df['cpf_limpo'].notna().sum()
            print(f"   ✅ CPFs encontrados via chave_matricula: {encontrou_cpf}/{len(df)}")
            
            # Substitui o CPF pelo encontrado no banco
            df['CPF'] = df['CPF_encontrado']
            
            # Remove colunas auxiliares
            df = df.drop(columns=['cpf_limpo', 'CPF_encontrado'])
        else:
            print("   ⚠️ Não foi possível buscar dados no banco")
       
        # Cria chave2 como CPF + Valor (para cruzar com holerites)
        df["chave2"] = df["CPF"].fillna('').astype(str) + df["Valor_Limpo"]
       
        return df


# ==================== FUNÇÕES PARA HOLERITE ====================
def extrair_dados_holerite(texto):
    """Tenta extrair dados do holerite usando múltiplos padrões de regex"""
    
    # Padrões para encontrar NOME e CPF
    padroes_nome_cpf = [
        r"NOME:\s*(.+?)\s*CPF:\s*(\d{11})",
        r"NOME:\s*(.+?)\s*CPF:\s*(\d{3}\.\d{3}\.\d{3}-\d{2})",
        r"NOME:\s*(.+?)\s*CPF:\s*([\d.]+)",
        r"IDENTIFICAÇÃO\s*NOME:\s*(.+?)\s*CPF:\s*(\d{11})",
        r"IDENTIFICAÇÃO\s*NOME:\s*(.+?)\s*CPF:\s*([\d.]+)",
    ]
    
    # Padrões para encontrar VALOR TOTAL
    padroes_valor = [
        r"TOTAL:\s*R?\$?\s*([\d.,]+)",
        r"TOTAL\s*R?\$?\s*([\d.,]+)",
        r"VALOR\s*TOTAL\s*R?\$?\s*([\d.,]+)",
        r"L[ÍI]QUIDO\s*R?\$?\s*([\d.,]+)",
        r"R?\$?\s*([\d.,]+)\s*$",
    ]
    
    nome_cpf_match = None
    for padrao in padroes_nome_cpf:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            nome_cpf_match = match
            break
    
    valor_match = None
    for padrao in padroes_valor:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            valor_match = match
            break
    
    return nome_cpf_match, valor_match


def processar_pdf_fonte(caminho_fonte):
    """Processa os PDFs fonte (holerites)"""
   
    dados = []
   
    if isinstance(caminho_fonte, str) and caminho_fonte.lower().endswith('.zip'):
        with zipfile.ZipFile(caminho_fonte, 'r') as zip_ref:
            for arquivo in zip_ref.namelist():
                if arquivo.lower().endswith('.pdf'):
                    try:
                        with zip_ref.open(arquivo) as pdf_file:
                            pdf_content = BytesIO(pdf_file.read())
                            processar_pdf_unico(pdf_content, os.path.basename(arquivo), dados)
                    except Exception as e:
                        print(f"Erro: {arquivo} - {e}")
   
    elif os.path.isdir(caminho_fonte):
        arquivos_pdf = [f for f in os.listdir(caminho_fonte) if f.lower().endswith(".pdf")]
        print(f"\n📁 Holerites: {len(arquivos_pdf)} arquivos")
       
        if arquivos_pdf:
            primeiro = arquivos_pdf[0]
            print("\n" + "="*60)
            print(f"📄 PRIMEIRO HOLERITE: {primeiro}")
            print("="*60)
           
            caminho_pdf = os.path.join(caminho_fonte, primeiro)
            with open(caminho_pdf, "rb") as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                texto = extrair_texto_pagina(pdf_reader, 0)
                print(texto[:1500])
                print("="*60)
                print()
               
                nome_cpf_match, valor_match = extrair_dados_holerite(texto)
                if nome_cpf_match:
                    print(f"✅ Nome: {nome_cpf_match.group(1).strip()}")
                    print(f"✅ CPF: {limpar_cpf(nome_cpf_match.group(2))}")
                if valor_match:
                    print(f"✅ Valor: {valor_match.group(1).strip()}")
                print()
       
        print("Processando holerites...", end=" ")
        for i, arquivo in enumerate(arquivos_pdf):
            if i % 50 == 0 and i > 0:
                print(f"{i}", end=" ")
            caminho_pdf = os.path.join(caminho_fonte, arquivo)
            try:
                with open(caminho_pdf, "rb") as pdf_file:
                    processar_pdf_unico(pdf_file, arquivo, dados)
            except Exception as e:
                pass
        print("✓")
   
    elif isinstance(caminho_fonte, str) and caminho_fonte.lower().endswith('.pdf'):
        try:
            with open(caminho_fonte, "rb") as pdf_file:
                processar_pdf_unico(pdf_file, os.path.basename(caminho_fonte), dados)
        except Exception as e:
            print(f"Erro: {e}")
   
    df = pd.DataFrame(dados)
    if not df.empty:
        print(f"✅ Holerites: {len(df)} registros extraídos")
       
        df["Valor_Limpo"] = df["Valor"].str.replace(".", "").str.replace(",", "").str.replace(" ", "")
        df["Valor_Limpo"] = df["Valor_Limpo"].str.replace(r'[^\d]', '', regex=True)
        
        # Limpa o CPF
        df['CPF_Limpo'] = df['CPF'].apply(limpar_cpf)
       
        # Cria chave1 (nome + valor) e chave2 (CPF + valor)
        df["chave1"] = df["Nome"].apply(
            lambda x: "".join(x.split()[:2]) if len(x.split()) >= 2 else x.replace(" ", "")
        ) + df["Valor_Limpo"]
        
        df["chave2"] = df["CPF_Limpo"] + df["Valor_Limpo"]
       
        print("\n📊 DF_HOLERITES (primeiros 5):")
        print(df[['Nome', 'CPF', 'Valor', 'chave1', 'chave2']].head())
        print(f"   Total: {len(df)} registros")
    else:
        print("⚠️ NENHUM dado extraído dos holerites!")
   
    return df


def processar_pdf_unico(pdf_file, nome_arquivo, dados):
    """Processa um único PDF de holerite"""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    num_paginas = len(pdf_reader.pages)
   
    for numero_pagina in range(num_paginas):
        texto = extrair_texto_pagina(pdf_reader, numero_pagina)
        nome_cpf_match, valor_match = extrair_dados_holerite(texto)
       
        if nome_cpf_match and valor_match:
            dados.append({
                "Nome": nome_cpf_match.group(1).strip(),
                "CPF": limpar_cpf(nome_cpf_match.group(2)),
                "Valor": valor_match.group(1).strip(),
                "Arquivo": nome_arquivo
            })


# ==================== FUNÇÕES DE MESCLAGEM E UNIÃO ====================
def mesclar_dataframes(df_principal, df_fonte):
    """Mescla os dataframes usando CPF + Valor como chave"""
   
    if df_principal.empty or df_fonte.empty:
        print("⚠️ DataFrames vazios")
        return pd.DataFrame(), pd.DataFrame()
   
    print("\n🔍 Mesclando...")
   
    # Estratégia 1: chave2 (CPF + valor)
    print("  Tentando chave2 (CPF + Valor)...", end=" ")
    df_merged = df_fonte.merge(df_principal[['chave2', 'Página']], on='chave2', how='left')
    df_com = df_merged.dropna(subset=['Página'])
    df_sem = df_merged[df_merged['Página'].isna()].drop(columns=['Página'])
    print(f"{len(df_com)} encontrados")
   
    # Estratégia 2: chave1 (nome + valor) - como fallback
    if not df_sem.empty:
        print("  Tentando chave1 (Nome + Valor)...", end=" ")
        if 'chave1' in df_principal.columns:
            df_merged2 = df_sem.merge(df_principal[['chave1', 'Página']], on='chave1', how='left')
            df_com2 = df_merged2.dropna(subset=['Página'])
            df_sem2 = df_merged2[df_merged2['Página'].isna()].drop(columns=['Página'])
            print(f"{len(df_com2)} encontrados")
           
            df_final = pd.concat([df_com, df_com2], ignore_index=True)
            df_sem_final = df_sem2
        else:
            print("chave1 não disponível")
            df_final = df_com
            df_sem_final = df_sem
    else:
        df_final = df_com
        df_sem_final = df_sem
   
    if not df_sem_final.empty:
        print(f"  ⚠️ {len(df_sem_final)} não encontrados")
   
    df_final = df_final[['Arquivo', 'Página', 'Nome']] if not df_final.empty else df_final
   
    return df_final, df_sem_final


def unir_pdfs(df_resultado, df_nao_encontrados, caminho_pdf_principal, caminho_fonte):
    """Une os PDFs"""
   
    pasta_unidos = os.path.join(os.path.dirname(caminho_fonte), "Unidos")
    os.makedirs(pasta_unidos, exist_ok=True)
   
    print(f"\n📁 Salvando em: {pasta_unidos}")
   
    if not df_nao_encontrados.empty:
        caminho_excel = os.path.join(pasta_unidos, "holerites_nao_encontrados.xlsx")
        df_export = df_nao_encontrados.copy()
        df_export['Motivo'] = 'Não encontrado no comprovante'
        colunas = ['Arquivo', 'Nome', 'CPF', 'Valor', 'chave1', 'chave2', 'Motivo']
        colunas_existentes = [col for col in colunas if col in df_export.columns]
        df_export = df_export[colunas_existentes]
        df_export.to_excel(caminho_excel, index=False)
        print(f"✅ {len(df_nao_encontrados)} não encontrados salvos")
   
    if df_resultado.empty:
        print("⚠️ Nenhum para unir")
        return
   
    pdf_principal = PdfReader(caminho_pdf_principal)
    pdfs_cache = {}
   
    print("Unindo PDFs...", end=" ")
    for i, (_, row) in enumerate(df_resultado.iterrows()):
        if i % 50 == 0 and i > 0:
            print(f"{i}", end=" ")
       
        nome_arquivo = row["Arquivo"]
        pagina_principal = int(row["Página"]) - 1
       
        if nome_arquivo not in pdfs_cache:
            if isinstance(caminho_fonte, str) and caminho_fonte.lower().endswith('.zip'):
                with zipfile.ZipFile(caminho_fonte, 'r') as zip_ref:
                    with zip_ref.open(nome_arquivo) as pdf_file:
                        pdf_content = BytesIO(pdf_file.read())
                        pdfs_cache[nome_arquivo] = PdfReader(pdf_content)
            else:
                caminho_pdf = os.path.join(caminho_fonte, nome_arquivo)
                pdfs_cache[nome_arquivo] = PdfReader(caminho_pdf)
       
        pdf_fonte = pdfs_cache[nome_arquivo]
        pdf_writer = PdfWriter()
        pdf_writer.add_page(pdf_principal.pages[pagina_principal])
        for pagina in pdf_fonte.pages:
            pdf_writer.add_page(pagina)
       
        nome_saida = f"{row['Nome']}.pdf".replace("/", "-").replace("\\", "-")
        caminho_saida = os.path.join(pasta_unidos, nome_saida)
       
        with open(caminho_saida, "wb") as arquivo_saida:
            pdf_writer.write(arquivo_saida)
   
    print(f"✓ {len(df_resultado)} arquivos gerados")


# ==================== CONFIGURAÇÃO E EXECUÇÃO ====================
if __name__ == "__main__":
    # CONFIGURAÇÃO DOS CAMINHOS - ALTERE AQUI CONFORME NECESSÁRIO
    caminho_pdf_principal = r"Y:\PRESTACAO DE CONTAS\EIXO RIO DE JANEIRO\EDUC. MESQUITA\Juntar\Corrigido\10062026 170615-Comprovantes-BB.pdf"
    caminho_fonte_pdfs = r"Y:\PRESTACAO DE CONTAS\EIXO RIO DE JANEIRO\EDUC. MESQUITA\Juntar\Corrigido\RPA"
   
    print("="*60)
    print("🚀 INICIANDO PROCESSAMENTO")
    print("="*60)
   
    print("\n📄 Processando comprovantes...")
    df_principal = processar_pdf_principal(caminho_pdf_principal)
   
    print("\n📄 Processando holerites...")
    df_fonte = processar_pdf_fonte(caminho_fonte_pdfs)
   
    if not df_principal.empty and not df_fonte.empty:
        print("\n🔗 Mesclando dados...")
        df_resultado, df_nao_encontrados = mesclar_dataframes(df_principal, df_fonte)
       
        print(f"\n📊 RESULTADO FINAL:")
        print(f"   Encontrados: {len(df_resultado)}")
        print(f"   Não encontrados: {len(df_nao_encontrados)}")
       
        if not df_resultado.empty:
            print("\n📋 DF_RESULTADO (primeiros 5):")
            print(df_resultado.head())
           
            print("\n📦 Unindo PDFs...")
            unir_pdfs(df_resultado, df_nao_encontrados, caminho_pdf_principal, caminho_fonte_pdfs)
           
            print("\n✅ Processo concluído!")
        else:
            print("\n⚠️ Nenhuma correspondência encontrada!")
    else:
        print("\n⚠️ Não foi possível concluir. Verifique:")
        if df_principal.empty:
            print("  - Comprovante: NENHUM dado extraído!")
            print("  - Verifique se o PDF está no formato esperado")
        if df_fonte.empty:
            print("  - Holerites: NENHUM dado extraído!")
            print("  - Verifique se os PDFs estão no formato esperado")
   
    print("\n" + "="*60)