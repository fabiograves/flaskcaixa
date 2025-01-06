from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'teste'


# Função para conectar ao banco de dados
def get_db_connection():
    conn = sqlite3.connect("banco_local.db")
    conn.row_factory = sqlite3.Row  # Permite acessar os resultados como dicionários
    return conn


def testar_conexao():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contas")
    result = cursor.fetchall()
    conn.close()
    for linha in result:
        print(linha['nome'], linha['saldo'])  # Exemplo de acesso direto aos campos
    print("---------------------------------------")
    for linha in result:
        print(dict(linha))  # Converte o sqlite3.Row em um dicionario e imprime
    return result

@app.route('/')
def index():
    contas = testar_conexao() # Chamado somente para mostrar no console os tipos de acessos
    if not contas:
        # Mensagem exibida para mostrar alguma situação/erro
        flash("Nenhuma conta encontrada no banco de dados.", "warning")
    else:
        flash(f"Total de {len(contas)} contas encontradas.", "success")

    # O contas=contas faz o contas receber o return do testar_conexao e
    # passar ele como parametro a pagina html chamando contas tambem
    return render_template('index.html', contas=contas)


@app.route("/criar_conta", methods=["GET", "POST"])
def criar_conta():
    if request.method == "POST":
        nome = request.form["nome"]
        senha = request.form["senha"]
        saldo_inicial = float(request.form["saldo_inicial"])

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO contas (nome, senha, saldo) VALUES (?, ?, ?)", (nome, senha, saldo_inicial))
            cursor.execute(
                "INSERT INTO historico (nome, descricao, data_hora) VALUES (?, ?, ?)",
                (nome, f"Depósito inicial: R$ {saldo_inicial}", datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            flash("Conta criada com sucesso!", "success")
            return redirect(url_for("index"))
        except sqlite3.IntegrityError:
            flash("Erro: Conta já existe.", "danger")
            return redirect(url_for("criar_conta"))

    return render_template("criar_conta.html")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8088)
