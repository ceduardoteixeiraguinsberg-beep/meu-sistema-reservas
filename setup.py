import sqlite3

def configurar_sistema_completo():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # 1. TABELA DE UTILIZADORES (Manter igual)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL
        )
    ''')

    # 2. TABELA DE RECURSOS (Novidade Aula 26)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT
        )
    ''')

    # 3. TABELA DE RESERVAS (Atualizada para usar recurso_id)
    # Mantemos o campo 'servico' apenas por compatibilidade, mas o foco é 'recurso_id'
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            recurso_id INTEGER,
            servico TEXT, 
            data TEXT NOT NULL,
            status TEXT DEFAULT 'Pendente',
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (recurso_id) REFERENCES recursos (id)
        )
    ''')

    # Limpar para teste limpo
    cursor.execute("DELETE FROM reservas")
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM recursos")

    # Inserir Utilizadores
    utilizadores = [
        ('Gustavo_Admin', '123', 'gustavo.admin@empresa.pt'), 
        ('Helena_Gestora', 'helen123', 'helena.gestao@empresa.pt')
    ]
    cursor.executemany("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", utilizadores)

    # Inserir Recursos de Exemplo (Aula 26)
    recursos_dados = [
        ('Sala de Reuniões A', 'Piso 1 - 10 pessoas'),
        ('Auditório Principal', 'Piso 0 - Projetor'),
        ('Projetor Portátil', 'Marca Epson'),
        ('Carrinho de Laptops', '15 unidades disponíveis')
    ]
    cursor.executemany("INSERT INTO recursos (nome, descricao) VALUES (?, ?)", recursos_dados)

    conn.commit()
    conn.close()
    print("Base de dados configurada com sucesso para a Aula 26!")

if __name__ == "__main__":
    configurar_sistema_completo()