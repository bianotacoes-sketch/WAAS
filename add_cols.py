import pyodbc
from db_config import DB_CONFIG

conn = pyodbc.connect(f"DRIVER={DB_CONFIG['driver']};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']}")
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE TESTE.USUARIOS ADD GERENCIAR_OFERTAS NVARCHAR(MAX) NULL, IMAGENS_SERVICOS NVARCHAR(MAX) NULL;")
    conn.commit()
    print("Columns added successfully.")
except Exception as e:
    print("Error:", e)
conn.close()
