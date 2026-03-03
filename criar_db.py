import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Criar a tabela de utilizadores
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        email TEXT NOT NULL
    )
''')

# Inserir um utilizador padrão para teste
cursor.execute("INSERT INTO users (username, password, email) VALUES ('admin', '123', 'admin@email.com')")

conn.commit()
conn.close()
print("Base de dados criada com sucesso!")