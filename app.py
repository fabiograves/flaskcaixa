from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
from flask import session
from functools import wraps
app = Flask(__name__)
app.secret_key = 'teste'

# Função para conectar ao banco de dados
def get_db_connection():
    conn = sqlite3.connect("banco_local.db")
    conn.row_factory = sqlite3.Row  # Permite acessar os resultados como dicionários
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "nome" not in session:
            flash("Você precisa estar logado para acessar esta página.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


"""def testar_conexao():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM historico)
    result = cursor.fetchall()
    for linha in result:
        print(linha['nome'], linha['descricao'], linha['data_hora'])
    print("---------------------------------------")
    for linha in result:
        print(dict(linha))  # Converte o sqlite3.Row em um dicionario e imprime
    conn.close()
    return result

@app.route('/')
def index():
    historico = testar_conexao() # Chamado somente para mostrar no console os tipos de acessos
    # O contas=contas faz o contas receber o return do testar_conexao e
    # passar ele como parametro a pagina html chamando contas tambem
    return render_template('index.html', contas=contas)"""

import re

def validar_cpf(cpf):
    # Remove todos os caracteres que não são números
    cpf = re.sub(r"\D", "", cpf)

    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False, None

    # Verifica se todos os dígitos são iguais (ex: 111.111.111-11, inválido)
    if cpf == cpf[0] * 11:
        return False, None

    # Cálculo dos dígitos verificadores
    def calcular_digito(cpf, peso):
        soma = sum(int(digito) * peso for digito, peso in zip(cpf, range(peso, 1, -1)))
        resto = soma % 11
        return "0" if resto < 2 else str(11 - resto)

    # Primeiro dígito verificador
    primeiro_digito = calcular_digito(cpf[:9], 10)
    # Segundo dígito verificador
    segundo_digito = calcular_digito(cpf[:10], 11)

    if cpf[9] == primeiro_digito and cpf[10] == segundo_digito:
        # Formata o CPF como XXX.XXX.XXX-XX
        cpf_formatado = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        return True, cpf_formatado

    return False, None
@app.route("/criar_conta", methods=["GET", "POST"])
def criar_conta():
    if request.method == "POST":
        nome = request.form["nome"]
        cpf = request.form["cpf"]
        senha = request.form["senha"]
        confirmar_senha = request.form["confirmar_senha"]
        saldo_inicial = float(request.form.get("saldo_inicial", 0) or 0)

        if not nome.strip():
            flash("O nome não pode estar vazio ou ser apenas espaços.", "danger")
            return redirect(url_for("criar_conta"))

        cpf_valido, cpf_formatado = validar_cpf(cpf)
        if not cpf_valido:
            flash("CPF inválido. Por favor, insira um CPF válido.", "danger")
            return redirect(url_for("criar_conta"))

        if senha != confirmar_senha:
            flash("Senha e Confirmar senha não são iguais.", "danger")
            return redirect(url_for("criar_conta"))

        if saldo_inicial < 0:
            flash("O saldo inicial não pode ser negativo.", "danger")
            return redirect(url_for("criar_conta"))

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
        except Exception as e:
            flash(f"Ocorreu um erro inesperado: {str(e)}", "danger")
            return redirect(url_for("criar_conta"))

    return render_template("criar_conta.html")

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        nome = request.form["nome"]
        senha = request.form["senha"]

        if not nome.strip():
            flash("O nome não pode estar vazio ou ser apenas espaços.", "danger")
            return redirect(url_for("criar_conta"))
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT senha FROM contas WHERE nome = ?", (nome,))
            senha_coletada = cursor.fetchone()[0]
            if senha_coletada == senha:
                flash("LOGIN REALIZADO COM SUCESSO!", "success")
                cursor.execute("UPDATE contas SET erro_senha = 0 WHERE nome = ?",
                               (nome,))
                conn.commit()
                session["nome"] = nome
                cursor.execute("SELECT saldo FROM contas WHERE nome = ?", (nome,))
                saldo_atual = cursor.fetchone()[0]
                session["saldo"] = saldo_atual
                conn.close()
                return redirect(url_for("home"))
            else:
                flash("A senha está incorreta!", "danger")
                cursor.execute("UPDATE contas SET erro_senha = erro_senha + 1 WHERE nome = ?", (nome,))
                conn.commit()
                conn.close()
                return redirect(url_for("login"))
        except Exception as e:
            flash(f"Ocorreu um erro inesperado: {str(e)}", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/home")
@login_required
def home():
    return render_template("home.html")

@app.route("/sacar" , methods=["GET", "POST"])
@login_required
def sacar():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == "POST":
        nome = session["nome"]
        saque = float(request.form["valor"])

        if not saque:
            flash("Esse campo não pode estar vazio ou ser apenas espaços.", "danger")
            return redirect(url_for("sacar"))
        elif saque <= 0:
            cursor.execute("SELECT saldo FROM contas WHERE nome = ?", (nome,))
            saldo_atual = cursor.fetchone()[0]
            flash("O valor para ser sacado não é válido!", "danger")
            return redirect(url_for("sacar", saldo=saldo_atual))
        try:
            cursor.execute("SELECT saldo FROM contas WHERE nome = ?", (nome,))
            saldo_atual = cursor.fetchone()[0]
            if saldo_atual < saque:
                flash("Não foi possível realizar o saque, o valor a ser sacado é maior do que o saldo atual!", "danger")
                return redirect(url_for("sacar", saldo=saldo_atual))
            else:
                novo_saldo = saldo_atual - saque
                cursor.execute("UPDATE contas SET saldo = ?, saques_diarios = ? WHERE nome = ?",
                               (novo_saldo, saque, nome))
                conn.commit()
                flash(f'Saque realizado com sucesso! O saldo atual é {novo_saldo}', "success")
                cursor.execute("INSERT INTO historico (nome, descricao, data_hora) VALUES (?, ?, ?)",
                               (nome, f"Sacado: R$ {saque}", datetime.now().isoformat()))
                conn.commit()
                return redirect(url_for("home"))

        except Exception as e:
            cursor.execute("SELECT saldo FROM contas WHERE nome = ?", (nome,))
            saldo_atual = cursor.fetchone()[0]
            flash(f"Ocorreu um erro inesperado: {str(e)}", "danger")
            return redirect(url_for("sacar", saldo=saldo_atual))

    nome = session["nome"]
    cursor.execute("SELECT saldo FROM contas WHERE nome = ?", (nome,))
    saldo_atual = cursor.fetchone()[0]
    conn.close()
    return render_template("sacar.html", saldo=saldo_atual)

@app.route("/depositar" , methods=["GET", "POST"])
@login_required
def depositar():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == "POST":
        deposito = float(request.form["valor"])
        nome = session["nome"]
        if not deposito:
            flash("Esse campo não pode estar vazio ou ser apenas espaços.", "danger")
            return redirect(url_for("depositar"))
        elif deposito <= 0:
            cursor.execute("SELECT saldo FROM contas WHERE nome = ?", (nome,))
            saldo_atual = cursor.fetchone()[0]
            flash("O valor para ser sacado não é válido!", "danger")
            return redirect(url_for("depositar", saldo=saldo_atual))
        try:
            cursor.execute("SELECT saldo FROM contas WHERE nome = ?", (nome,))
            saldo_atual = cursor.fetchone()[0]
            novo_saldo = saldo_atual + deposito
            cursor.execute("UPDATE contas set saldo = ? WHERE nome = ?", (novo_saldo, nome))
            conn.commit()
            flash(f"Depóstito realizado com sucesso! O saldo atual é {novo_saldo}", "success")
            cursor.execute("INSERT INTO historico (nome, descricao, data_hora) VALUES (?, ?, ?)",
                           (nome, f"Depositado: R$ {deposito}", datetime.now().isoformat()))
            conn.commit()
            return redirect(url_for("home"))
        except Exception as e:
            cursor.execute("SELECT saldo FROM contas WHERE nome = ?", (nome,))
            saldo_atual = cursor.fetchone()[0]
            flash(f"Ocorreu um erro inesperado: {str(e)}", "danger")
            return redirect(url_for("depositar", saldo=saldo_atual))

    nome = session["nome"]
    cursor.execute("SELECT saldo FROM contas WHERE nome = ?", (nome,))
    saldo_atual = cursor.fetchone()[0]
    conn.close()
    return render_template("depositar.html", saldo=saldo_atual)

@app.route("/transferir" , methods=["GET", "POST"])
@login_required
def transferir():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == "POST":
        transferencia = float(request.form["valor"])
        destino = request.form["destinatario"]
        origem = session["nome"]
        cursor.execute("SELECT saldo FROM contas WHERE nome = ?", (origem,))
        saldo_atual = cursor.fetchone()[0]
        if saldo_atual >= transferencia:
            novo_saldo = saldo_atual - transferencia
            cursor.execute("UPDATE contas SET saldo = ? WHERE nome = ?", (novo_saldo, origem))
            conn.commit()
            cursor.execute("SELECT saldo FROM contas WHERE nome = ?", (destino,))
            saldo_destinatario = cursor.fetchone()[0]
            novo_saldo_destinatario = saldo_destinatario + transferencia
            cursor.execute("UPDATE contas SET saldo = ? WHERE nome = ?", (novo_saldo_destinatario, destino))
            conn.commit()
            flash(f'Você transferiu R${transferencia} para {destino}', "success")
            cursor.execute("INSERT INTO historico (nome, descricao, data_hora) VALUES (?, ?, ?)",
                           (origem, f"Transferido para {destino}: R$ {transferencia}", datetime.now().isoformat()))
            conn.commit()
            return redirect(url_for("home", saldo=saldo_atual))
        else:
            flash("O saldo atual não é o suficiente", "danger")

    nome = session["nome"]
    cursor.execute("SELECT saldo FROM contas WHERE nome = ?", (nome,))
    saldo_atual = cursor.fetchone()[0]
    conn.close()
    return render_template("transferir.html", saldo=saldo_atual)

@app.route("/extrato")
@login_required
def extrato():
    conn = get_db_connection()
    cursor = conn.cursor()
    nome = session["nome"]
    cursor.execute("SELECT * FROM historico WHERE nome = ?", (nome,))
    extrato = cursor.fetchall()
    print(extrato)
    cursor.execute("SELECT saldo FROM contas WHERE nome = ?", (nome,))
    saldo_atual = cursor.fetchone()[0]
    conn.close()
    return render_template("extrato.html", saldo=saldo_atual, extrato=extrato)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8088)
