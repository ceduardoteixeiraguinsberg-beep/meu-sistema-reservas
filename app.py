from flask import Flask, render_template, request, session, redirect, url_for, flash # Adicionado flash
from functools import wraps
import sqlite3 
from datetime import datetime # Necessário para validar datas
import os # ACRESCENTADO PARA AULA 29 (DEPLOY)

app = Flask(__name__,
            static_folder='Static',
            template_folder='Templates')

# ACRESCENTADO: Garantir que a chave mestra funciona em qualquer ambiente
app.secret_key = os.environ.get('SECRET_KEY', 'chave_mestra_aula_29_deploy')

# ---------------------------------------------------------
# CONFIGURAÇÃO DA BASE DE DATOS
# ---------------------------------------------------------
def get_db_connection():
    # ACRESCENTADO: Melhoria no caminho da base de dados para o servidor
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  
    return conn

# ---------------------------------------------------------
# DECORADOR DE PROTEÇÃO
# ---------------------------------------------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

# ---------------------------------------------------------
# ROTAS PÚBLICAS
# ---------------------------------------------------------
@app.route("/")
def home():
    return render_template("index3.html")

@app.route("/sobre")
def sobre():
    return render_template("sobre.html")

@app.route("/contactos")
def contactos():
    return render_template("contactos.html")

@app.route("/contacto/enviar", methods=["POST"])
def enviar_contacto():
    try:
        nome = request.form.get("nome")
        email = request.form.get("email")
        msg = request.form.get("mensagem")
        flash(f"Obrigado {nome}, a sua mensagem foi enviada com sucesso!", "success") # Aula 28
        return render_template("resultado_contacto.html", nome=nome, email=email, mensagem=msg)
    except Exception as e:
        return f"Erro: {e}", 500

# ---------------------------------------------------------
# LOGIN E LOGOUT
# ---------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                         (username, password)).fetchone()
        conn.close()

        if user:
            session["user"] = user['username']
            session["user_id"] = user['id']
            flash(f"Bem-vindo de volta, {user['username']}!", "success") # Aula 28
            if user['username'] == "Gustavo_Admin":
                return redirect(url_for("dashboard"))
            return redirect(url_for("listar_reservas"))
        else:
            flash("Credenciais inválidas. Tente novamente.", "danger") # Aula 28
            return render_template("login.html", erro="Credenciais inválidas")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear() 
    flash("Sessão encerrada.", "info") # Aula 28
    return redirect(url_for("home"))

# ---------------------------------------------------------
# CRUD DE RESERVAS (AULAS 25, 26, 27 & 28)
# ---------------------------------------------------------

@app.route("/reservas")
@login_required
def listar_reservas():
    conn = get_db_connection()
    
    filtro_recurso = request.args.get('recurso_id')
    filtro_data = request.args.get('data')

    query = '''
        SELECT reservas.*, recursos.nome AS recurso_nome 
        FROM reservas 
        LEFT JOIN recursos ON reservas.recurso_id = recursos.id
        WHERE reservas.user_id = ?
    '''
    parametros = [session["user_id"]]

    if filtro_recurso:
        query += " AND reservas.recurso_id = ?"
        parametros.append(filtro_recurso)
    
    if filtro_data:
        query += " AND reservas.data LIKE ?"
        parametros.append(f"{filtro_data}%")

    query += " ORDER BY reservas.data DESC"
    
    minhas_reservas = conn.execute(query, parametros).fetchall()
    recursos = conn.execute('SELECT * FROM recursos').fetchall()
    
    conn.close()
    return render_template("reservas.html", reservas=minhas_reservas, recursos=recursos)

@app.route("/reservas/nova", methods=["GET", "POST"])
@login_required
def nova_reserva():
    conn = get_db_connection()
    
    if request.method == "POST":
        recurso_id = request.form.get("recurso_id")
        servico = request.form.get("servico") 
        data_str = request.form.get("data")
        user_id = session["user_id"]

        if not recurso_id or not data_str:
            recursos = conn.execute('SELECT * FROM recursos').fetchall()
            flash("Todos os campos são obrigatórios!", "warning") # Aula 28
            return render_template("criar_reserva.html", erro="Campos obrigatórios!", recursos=recursos)

        try:
            data_reserva = datetime.strptime(data_str, '%Y-%m-%dT%H:%M')
            agora = datetime.now()

            if data_reserva < agora:
                recursos = conn.execute('SELECT * FROM recursos').fetchall()
                flash("Não pode agendar no passado!", "danger") # Aula 28
                return render_template("criar_reserva.html", erro="Data inválida!", recursos=recursos)

            conflito = conn.execute('SELECT * FROM reservas WHERE data = ? AND recurso_id = ?',
                                   (data_str, recurso_id)).fetchone()
            
            if conflito:
                recursos = conn.execute('SELECT * FROM recursos').fetchall()
                flash("Este horário já está ocupado para este recurso!", "danger") # Aula 28
                return render_template("criar_reserva.html", erro="Conflito de horário!", recursos=recursos)

            conn.execute('INSERT INTO reservas (user_id, recurso_id, servico, data) VALUES (?, ?, ?, ?)',
                         (user_id, recurso_id, servico, data_str))
            conn.commit()
            conn.close()
            flash("Reserva criada com sucesso!", "success") # Aula 28
            return redirect(url_for('listar_reservas'))
        except ValueError:
            recursos = conn.execute('SELECT * FROM recursos').fetchall()
            return render_template("criar_reserva.html", erro="Formato de data inválido!", recursos=recursos)

    recursos = conn.execute('SELECT * FROM recursos').fetchall()
    conn.close()
    return render_template("criar_reserva.html", recursos=recursos)

@app.route("/reservas/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_reserva(id):
    conn = get_db_connection()
    reserva = conn.execute('SELECT * FROM reservas WHERE id = ? AND user_id = ?', 
                          (id, session["user_id"])).fetchone()

    if request.method == "POST":
        novo_servico = request.form.get("servico")
        nova_data = request.form.get("data")
        
        conn.execute('UPDATE reservas SET servico = ?, data = ? WHERE id = ?',
                     (novo_servico, nova_data, id))
        conn.commit()
        conn.close()
        flash("Reserva atualizada com sucesso!", "success") # Aula 28
        return redirect(url_for('listar_reservas'))

    conn.close()
    return render_template("edit_reserva.html", reserva=reserva)

@app.route("/reservas/delete/<int:id>")
@login_required
def delete_reserva(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM reservas WHERE id = ? AND user_id = ?', 
                 (id, session["user_id"]))
    conn.commit()
    conn.close()
    flash("Reserva cancelada com sucesso.", "info") # Aula 28
    return redirect(url_for('listar_reservas'))

# ---------------------------------------------------------
# AULA 28: RELATÓRIOS (NOVO)
# ---------------------------------------------------------

@app.route("/relatorios")
@login_required
def relatorios_dashboard():
    conn = get_db_connection()
    recursos = conn.execute('SELECT * FROM recursos').fetchall()
    conn.close()
    return render_template("relatorios.html", recursos=recursos)

@app.route("/relatorio/recurso/<int:id>")
@login_required
def relatorio_recurso(id):
    conn = get_db_connection()
    recurso = conn.execute('SELECT * FROM recursos WHERE id = ?', (id,)).fetchone()
    
    reservas = conn.execute('''
        SELECT reservas.*, users.username 
        FROM reservas 
        JOIN users ON reservas.user_id = users.id 
        WHERE recurso_id = ? 
        ORDER BY data DESC
    ''', (id,)).fetchall()
    
    total_reservas = len(reservas)
    
    conn.close()
    return render_template("relatorio_detalhado.html", 
                           recurso=recurso, 
                           reservas=reservas, 
                           total=total_reservas)

# ---------------------------------------------------------
# GESTÃO DE UTILIZADORES (APENAS ADMIN)
# ---------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    if session.get("user") != "Gustavo_Admin":
        return redirect(url_for('listar_reservas'))
    return render_template("dashboard.html")

@app.route("/users")
@login_required
def list_users():
    if session.get("user") != "Gustavo_Admin":
        return redirect(url_for('listar_reservas'))
    conn = get_db_connection()
    usuarios = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return render_template("users.html", usuarios=usuarios)

@app.route("/edit_user/<int:id>", methods=["GET", "POST"])
@login_required
def edit_user(id):
    if session.get("user") != "Gustavo_Admin":
        return redirect(url_for('listar_reservas'))
    conn = get_db_connection()
    usuario = conn.execute('SELECT * FROM users WHERE id = ?', (id,)).fetchone()
    if request.method == "POST":
        conn.execute('UPDATE users SET username = ?, email = ? WHERE id = ?',
                     (request.form.get("username"), request.form.get("email"), id))
        conn.commit()
        conn.close()
        flash("Utilizador atualizado!", "success")
        return redirect(url_for('list_users'))
    conn.close()
    return render_template("edit.html", usuario=usuario)

@app.route("/delete/<int:id>")
@login_required
def delete_user(id):
    if session.get("user") != "Gustavo_Admin":
        return redirect(url_for('listar_reservas'))
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash("Utilizador removido.", "warning")
    return redirect(url_for('list_users'))

# ---------------------------------------------------------
# PERFIL E IMC
# ---------------------------------------------------------
@app.route("/perfil")
@login_required
def perfil():
    nome_usuario = session.get("user")
    lista_hobbies = ["Programar Python", "Gerir Bases de Dados", "Desenvolver Flask"]
    idade_usuario = 20 
    return render_template("perfil.html", nome=nome_usuario, hobbies=lista_hobbies, idade=idade_usuario)

@app.route("/imc")
@login_required
def imc_page():
    return render_template("imc.html")

@app.route("/calcular_imc", methods=["POST"])
@login_required
def calcular_imc():
    try:
        peso = float(request.form.get("peso"))
        altura = float(request.form.get("altura"))
        imc_valor = round(peso / (altura * altura), 2)
        cat = "Peso normal" if imc_valor < 25 else "Acima do peso"
        return render_template("resultado_imc.html", imc=imc_valor, categoria=cat)
    except:
        flash("Erro ao calcular IMC. Verifique os dados.", "danger")
        return "Erro nos dados!", 400

# ---------------------------------------------------------
# ACRESCENTADO: CONFIGURAÇÃO DE PORTA PARA DEPLOY (AULA 29)
# ---------------------------------------------------------
if __name__ == "__main__":
    # O Render usa a variável de ambiente PORT. Se não existir, usa 5000 (local)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False) # debug=False é mais seguro online