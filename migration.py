import pyodbc
from db_config import DB_CONFIG

def run_migration():
    print("Iniciando migração de banco de dados...")
    conn_str = f"DRIVER={DB_CONFIG['driver']};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']}"
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'TESTE' AND TABLE_NAME = 'CLIENTES' AND COLUMN_NAME = 'LAYOUT_CONFIG'
        """)
        
        existe = cursor.fetchone()[0] > 0
        
        if not existe:
            print("Adicionando coluna LAYOUT_CONFIG à tabela TESTE.CLIENTES...")
            cursor.execute("ALTER TABLE TESTE.CLIENTES ADD LAYOUT_CONFIG NVARCHAR(MAX) NULL;")
            conn.commit()
            print("Coluna LAYOUT_CONFIG adicionada com sucesso!")
        else:
            print("A coluna LAYOUT_CONFIG já existe na tabela TESTE.CLIENTES.")
            
        # Verificar se a coluna PERSONALIZAR_APARENCIA já existe
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'TESTE' AND TABLE_NAME = 'USUARIOS' AND COLUMN_NAME = 'PERSONALIZAR_APARENCIA'
        """)
        
        existe_perm = cursor.fetchone()[0] > 0
        
        if not existe_perm:
            print("Adicionando coluna PERSONALIZAR_APARENCIA à tabela TESTE.USUARIOS...")
            cursor.execute("ALTER TABLE TESTE.USUARIOS ADD PERSONALIZAR_APARENCIA NVARCHAR(MAX) NULL;")
            conn.commit()
            print("Coluna PERSONALIZAR_APARENCIA adicionada com sucesso!")
        else:
            print("A coluna PERSONALIZAR_APARENCIA já existe na tabela TESTE.USUARIOS.")
            
        # Verificar se a coluna ATIVO já existe na tabela TESTE.USUARIOS
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'TESTE' AND TABLE_NAME = 'USUARIOS' AND COLUMN_NAME = 'ATIVO'
        """)
        
        existe_ativo = cursor.fetchone()[0] > 0
        
        if not existe_ativo:
            print("Adicionando coluna ATIVO à tabela TESTE.USUARIOS...")
            cursor.execute("ALTER TABLE TESTE.USUARIOS ADD ATIVO VARCHAR(1) DEFAULT 'S' NULL;")
            conn.commit()
            # Garantir que todos os existentes fiquem como 'S'
            cursor.execute("UPDATE TESTE.USUARIOS SET ATIVO = 'S';")
            conn.commit()
            print("Coluna ATIVO adicionada com sucesso!")
        else:
            print("A coluna ATIVO já existe na tabela TESTE.USUARIOS.")
            
        # Verificar e criar o site_id 4 se não existir
        cursor.execute("SELECT COUNT(*) FROM TESTE.SITE WHERE ID = 4")
        if cursor.fetchone()[0] == 0:
            print("Adicionando tipo de site Imobiliária (id=4)...")
            cursor.execute("SET IDENTITY_INSERT TESTE.SITE ON; INSERT INTO TESTE.SITE (ID, NOME) VALUES (4, 'Imobiliária'); SET IDENTITY_INSERT TESTE.SITE OFF;")
            conn.commit()

        # Criar tabela teste.imobiliaria
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'teste' AND TABLE_NAME = 'imobiliaria'
        """)
        if cursor.fetchone()[0] == 0:
            print("Criando tabela teste.imobiliaria...")
            cursor.execute("""
            CREATE TABLE teste.imobiliaria (
                id INT IDENTITY(1,1) PRIMARY KEY,
                site_id INT,
                empresa_id INT,
                ofertas NVARCHAR(MAX),
                ativo VARCHAR(1),
                data_criacao DATE,
                data_fim DATE
            );
            """)
            conn.commit()

        # Criar tabela teste.imobiliaria_imagens
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'teste' AND TABLE_NAME = 'imobiliaria_imagens'
        """)
        if cursor.fetchone()[0] == 0:
            print("Criando tabela teste.imobiliaria_imagens...")
            cursor.execute("""
            CREATE TABLE teste.imobiliaria_imagens (
                id INT IDENTITY(1,1) PRIMARY KEY,
                oferta_id INT,
                imagem1 VARBINARY(MAX), imagem2 VARBINARY(MAX), imagem3 VARBINARY(MAX), imagem4 VARBINARY(MAX), imagem5 VARBINARY(MAX),
                imagem6 VARBINARY(MAX), imagem7 VARBINARY(MAX), imagem8 VARBINARY(MAX), imagem9 VARBINARY(MAX), imagem10 VARBINARY(MAX),
                imagem11 VARBINARY(MAX), imagem12 VARBINARY(MAX), imagem13 VARBINARY(MAX), imagem14 VARBINARY(MAX), imagem15 VARBINARY(MAX),
                imagem16 VARBINARY(MAX), imagem17 VARBINARY(MAX), imagem18 VARBINARY(MAX), imagem19 VARBINARY(MAX), imagem20 VARBINARY(MAX),
                imagem21 VARBINARY(MAX), imagem22 VARBINARY(MAX), imagem23 VARBINARY(MAX), imagem24 VARBINARY(MAX), imagem25 VARBINARY(MAX),
                imagem26 VARBINARY(MAX), imagem27 VARBINARY(MAX), imagem28 VARBINARY(MAX), imagem29 VARBINARY(MAX), imagem30 VARBINARY(MAX)
            );
            """)
            conn.commit()

        # Criar tabela teste.imagens
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'teste' AND TABLE_NAME = 'imagens'
        """)
        if cursor.fetchone()[0] == 0:
            print("Criando tabela teste.imagens...")
            cursor.execute("""
            CREATE TABLE teste.imagens (
                id INT IDENTITY(1,1) PRIMARY KEY,
                empresa_id int,
                site_id int,
                servico_id int,
                imagem1 VARBINARY(MAX), imagem2 VARBINARY(MAX), imagem3 VARBINARY(MAX), imagem4 VARBINARY(MAX), imagem5 VARBINARY(MAX),
                imagem6 VARBINARY(MAX), imagem7 VARBINARY(MAX), imagem8 VARBINARY(MAX), imagem9 VARBINARY(MAX), imagem10 VARBINARY(MAX),
                imagem11 VARBINARY(MAX), imagem12 VARBINARY(MAX), imagem13 VARBINARY(MAX), imagem14 VARBINARY(MAX), imagem15 VARBINARY(MAX)
            );
            """)
            conn.commit()

        # Verificar se a coluna comentarios existe em teste.imagens
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'teste' AND TABLE_NAME = 'imagens' AND COLUMN_NAME = 'comentarios'
        """)
        if cursor.fetchone()[0] == 0:
            print("Adicionando coluna comentarios à tabela teste.imagens...")
            cursor.execute("ALTER TABLE teste.imagens ADD comentarios NVARCHAR(MAX) NULL;")
            conn.commit()

        # Verificar se a coluna ENDERECO existe em TESTE.EMPRESA
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'TESTE' AND TABLE_NAME = 'EMPRESA' AND COLUMN_NAME = 'ENDERECO'
        """)
        if cursor.fetchone()[0] == 0:
            print("Adicionando coluna ENDERECO à tabela TESTE.EMPRESA...")
            cursor.execute("ALTER TABLE TESTE.EMPRESA ADD ENDERECO NVARCHAR(MAX) NULL;")
            conn.commit()

        # Verificar se a coluna SITE_ID existe em TESTE.EMPRESA
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'TESTE' AND TABLE_NAME = 'EMPRESA' AND COLUMN_NAME = 'SITE_ID'
        """)
        if cursor.fetchone()[0] == 0:
            print("Adicionando coluna SITE_ID à tabela TESTE.EMPRESA...")
            cursor.execute("ALTER TABLE TESTE.EMPRESA ADD SITE_ID INT NULL;")
            conn.commit()

        # Criar ou atualizar tabela teste.buffets
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'teste' AND TABLE_NAME = 'buffets'
        """)
        if cursor.fetchone()[0] == 0:
            print("Criando tabela teste.buffets...")
            cursor.execute("""
            CREATE TABLE teste.buffets (
                id INT IDENTITY(1,1) PRIMARY KEY,
                site_id INT,
                empresa_id INT,
                nome_cliente NVARCHAR(255),
                prazo DATE,
                servico_id INT,
                observacoes NVARCHAR(MAX)
            );
            """)
            conn.commit()
        else:
            print("Atualizando colunas da tabela teste.buffets...")
            cursor.execute("ALTER TABLE teste.buffets ALTER COLUMN observacoes NVARCHAR(MAX) NULL;")
            cursor.execute("ALTER TABLE teste.buffets ALTER COLUMN nome_cliente NVARCHAR(255) NULL;")
            conn.commit()

        # Verificar se a coluna CARROSSEL_IMAGENS já existe em TESTE.USUARIOS
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'TESTE' AND TABLE_NAME = 'USUARIOS' AND COLUMN_NAME = 'CARROSSEL_IMAGENS'
        """)
        
        existe_carrossel_perm = cursor.fetchone()[0] > 0
        
        if not existe_carrossel_perm:
            print("Adicionando coluna CARROSSEL_IMAGENS à tabela TESTE.USUARIOS...")
            cursor.execute("ALTER TABLE TESTE.USUARIOS ADD CARROSSEL_IMAGENS NVARCHAR(MAX) NULL;")
            conn.commit()
            print("Coluna CARROSSEL_IMAGENS adicionada com sucesso!")
        else:
            print("A coluna CARROSSEL_IMAGENS já existe na tabela TESTE.USUARIOS.")

        # Criar tabela teste.carrossel
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'teste' AND TABLE_NAME = 'carrossel'
        """)
        if cursor.fetchone()[0] == 0:
            print("Criando tabela teste.carrossel...")
            cursor.execute("""
            CREATE TABLE teste.carrossel (
                id INT IDENTITY(1,1) PRIMARY KEY,
                empresa_id INT,
                site_id INT,
                imagem1 VARBINARY(MAX), imagem2 VARBINARY(MAX), imagem3 VARBINARY(MAX), imagem4 VARBINARY(MAX), imagem5 VARBINARY(MAX),
                imagem6 VARBINARY(MAX), imagem7 VARBINARY(MAX), imagem8 VARBINARY(MAX), imagem9 VARBINARY(MAX), imagem10 VARBINARY(MAX)
            );
            """)
            conn.commit()
            print("Tabela teste.carrossel criada com sucesso!")
        else:
            print("A tabela teste.carrossel já existe.")

        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao executar migração: {e}")
        return False

if __name__ == '__main__':
    run_migration()
