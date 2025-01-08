import sqlite3

# Conecta ao banco de dados ou cria o arquivo banco_local.db
conn = sqlite3.connect("banco_local.db")
cursor = conn.cursor()

# Cria a tabela "contas"
cursor.execute("""
CREATE TABLE IF NOT EXISTS contas (
    nome TEXT PRIMARY KEY,
    senha TEXT NOT NULL,
    erro_senha INTEGER DEFAULT 0,
    saldo REAL NOT NULL,
    saques_diarios REAL DEFAULT 0,
    cpf VARCHAR[14] NOT NULL
)
""")

# Cria a tabela "historico"
cursor.execute("""
CREATE TABLE IF NOT EXISTS historico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT NOT NULL,
    data_hora TEXT NOT NULL,
    FOREIGN KEY (nome) REFERENCES contas (nome)
)
""")

# Confirma as alterações e fecha a conexão
conn.commit()
conn.close()

print("Banco de dados criado com sucesso!")
