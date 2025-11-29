v
# ==========================================================
# ROTA PRINCIPAL — CARREGA O FORMULÁRIO
# ==========================================================
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", horarios=[], mensagem=None)


# ==========================================================
# ROTA PARA VERIFICAR HORÁRIOS OCUPADOS
# ==========================================================
@app.route("/horarios_indisponiveis", methods=["POST"])
def horarios_indisponiveis():
    data = request.form.get("data")

    if not data:
        return jsonify({"ocupados": []})

    # Lê todas as linhas da planilha
    registros = sheet.get_all_records()

    ocupados = [
        r["horario"]
        for r in registros
        if str(r["data"]).strip() == data
    ]

    return jsonify({"ocupados": ocupados})


# ==========================================================
# RECEBER FORMULÁRIO DO SITE
# ==========================================================
@app.route("/enviar", methods=["POST"])
def enviar():
    data = request.form.get("data")
    horario = request.form.get("horario")
    responsavel = request.form.get("responsavel")
    numero_criancas = request.form.get("numero_criancas")
    email = request.form.get("email")
    telefone = request.form.get("telefone")
    valor_total = request.form.get("valor_total")
    status_pagamento = request.form.get("status_pagamento")
    observacoes = request.form.get("observacoes")
    endereco = request.form.get("endereco")
    bairro = request.form.get("bairro")
    cidade = request.form.get("cidade")

    # gravação na planilha
    sheet.append_row([
        data, horario, responsavel, numero_criancas, email, telefone,
        valor_total, status_pagamento, observacoes, endereco, bairro, cidade
    ])

    return render_template("index.html", horarios=[], mensagem="Reserva enviada com sucesso!")


# ==========================================================
# EXECUÇÃO LOCAL
# ==========================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)


