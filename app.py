from flask import Flask, request, jsonify, render_template
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

app = Flask(__name__)

# ============================
#   GOOGLE CREDENTIALS
# ============================
google_credentials_json = os.getenv("GOOGLE_CREDENTIALS")

if not google_credentials_json:
    raise Exception("ERRO: A variável GOOGLE_CREDENTIALS não está definida no Render!")

creds_dict = json.loads(google_credentials_json)

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# ============================
#   PLANILHA
# ============================
SHEET_ID = "10HFxgC2k_6VkFyUoTiPMg6h0aBUhUaESYg5knbapktM"
sheet = client.open_by_key(SHEET_ID).sheet1


# ============================
#   ROTA DO FORMULÁRIO WEB
# ============================
@app.route("/", methods=["GET"])
def formulario():
    return render_template("index.html")


# ============================
#   ROTA PARA RECEBER FORMULÁRIO
# ============================
@app.route("/enviar", methods=["POST"])
def enviar():
    nome = request.form.get("nome")
    telefone = request.form.get("telefone")
    data_reserva = request.form.get("data")
    horario = request.form.get("horario")
    pacote = request.form.get("pacote")

    if not nome or not telefone:
        return "Erro: nome e telefone são obrigatórios."

    sheet.append_row([nome, telefone, data_reserva, horario, pacote])

    return "<h2>Reserva enviada com sucesso!</h2>"


# ============================
#   ROTA DO BOT TELEGRAM
# ============================
@app.route("/reserva", methods=["POST"])
def receber_reserva():
    data = request.json

    nome = data.get("nome")
    telefone = data.get("telefone")
    data_reserva = data.get("data")
    horario = data.get("horario")
    pacote = data.get("pacote")

    if not nome or not telefone:
        return jsonify({"erro": "Nome e telefone são obrigatórios"}), 400

    sheet.append_row([nome, telefone, data_reserva, horario, pacote])

    return jsonify({"status": "OK", "mensagem": "Reserva registrada com sucesso!"})


# ============================
#   EXECUÇÃO LOCAL
# ============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
