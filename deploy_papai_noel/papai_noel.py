from flask import Flask, render_template, request, redirect
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

app = Flask(__name__)

# --------------------------------------------------------
# FUNÇÃO PARA GERAR HORÁRIOS AUTOMÁTICOS
# --------------------------------------------------------
def gerar_horarios():
    horarios = []
    inicio = datetime(2025, 12, 24, 14, 0)
    fim = datetime(2025, 12, 25, 11, 0)
    passo = timedelta(minutes=2)
    atual = inicio

    while atual <= fim:
        horarios.append(atual.strftime("%d/%m/%Y %H:%M"))
        atual += passo

    return horarios

# --------------------------------------------------------
# CONFIGURAÇÃO DO GOOGLE SHEETS
# --------------------------------------------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
client = gspread.authorize(creds)

# NOME EXATO DA PLANILHA NO GOOGLE SHEETS
sheet = client.open("Respostas do formulário - Reserva - Papai Noel Paulo Duarte").sheet1

# --------------------------------------------------------
# ROTAS
# --------------------------------------------------------
@app.route("/")
def index():
    horarios = gerar_horarios()
    return render_template("index.html", horarios=horarios)

@app.route("/enviar", methods=["POST"])
def enviar():
    dados = [
        request.form["data"],
        request.form["horario"],
        request.form["responsavel"],
        request.form["numero_criancas"],
        request.form["email"],
        request.form["telefone"],
        request.form["valor_total"],
        request.form["status_pagamento"],
        request.form["observacoes"],
        request.form["endereco"],
        request.form["bairro"],
        request.form["cidade"]
    ]

    sheet.append_row(dados)
    return redirect("/sucesso")

@app.route("/sucesso")
def sucesso():
    return "<h1>Agendamento enviado com sucesso!</h1>"

@app.route("/erro")
def erro():
    return "<h1>Ocorreu um erro no envio.</h1>"

# --------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
