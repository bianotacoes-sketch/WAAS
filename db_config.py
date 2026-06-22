import pyodbc
import os

# Configuração do banco de dados
DB_CONFIG = {
    'server': 'SRV-BI-01',
    'database': 'DW',
    'username': 'sa',
    'password': 'T@dala!@#40',
    'driver': '{ODBC Driver 17 for SQL Server}'
}

def get_db_connection():
    """Retorna uma conexão com o banco de dados"""
    try:
        conn_str = f"DRIVER={DB_CONFIG['driver']};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']}"
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco: {e}")
        return None

def init_database():
    """Apenas testa a conexão com o banco"""
    conn = get_db_connection()
    if not conn:
        print("Erro: Não foi possível conectar ao banco de dados")
        return False
    
    print("Banco de dados conectado com sucesso!")
    conn.close()
    return True