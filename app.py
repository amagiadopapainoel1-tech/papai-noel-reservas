from flask import Flask, render_template, request, jsonify
import smtplib
from email.message import EmailMessage
import os
from datetime import datetime

app = Flask(__name__)

# --------------------------
#  CONFIGURAÇÕES DO SISTEMA
# --------------------------

EMAIL_ORIGEM = "amagiadopapainoel1@gmail.com"
SENHA_EMAIL = "SUA_SENHA_DE_APP_AQUI"  # coloque aqui a senha de app do Gmail

PIX_COPIA_COLA = """00020126360014br.gov.bcb.pix0114+55419975658825204000053039865802BR5912PAULO_DUARTE6008Curitiba610981550-bc1qruqmcx20vwhv5dav2hlr4yg9n20kqz0fescezh"""

VALOR_POR_CRIANCA = 50

# Horários padrão
HORARIOS = [
    "18:00", "18:30", "19:00",
    "19:30", "20:00", "20:30",
    "21:00", "21:30", "22:00",
]

# Armazena reservas em memória (substituível por banco depois)
reservas = []


# ------------------------------------
#  FUNÇÃO PARA ENVIAR O E‑MAIL
# ------------------------------------
def enviar_email_confirmacao(dados, anexo_krcode, anexo_noel):
    msg = EmailMessage()
    msg["Subject"] = "Confirmação do Agendamento - Papai Noel 🎅"
    msg["From"] = EMAIL_ORIGEM
    msg["To"] = dados["email"]

    corpo = f"""
Olá {dados['responsavel']},

Sua reserva foi registrada com sucesso na
**Central de Distribuição de Presentes do Papai Noel** 🎄✨

Aqui estão os dados:

📅 **Data:** {dados['data_formatada']}
⏰ **Horário:** {dados['horario']}
👧👦 **Número de crianças:** {dados['numero_criancas']}
💰 **Valor Total:** R$ {dados['valor_total']:.2f}

---

## 🔔 *Instruções de Pagamento*

Você pode realizar o pagamento de duas formas:

### ✔ Pix Copia e Cola:
{PIX_COPIA_COLA}

### ✔ KR Code (QR Code):
(Imagem anexada neste e-mail)

---

Após o pagamento, envie o comprovante para:
📧 *amagiadopapainoel1@gmail.com*  
📱 *WhatsApp: (41) 99756-5882*

E **não esqueça**:
> "Ao enviar o comprovante, cite o nome da criança e descreva o presente.  
> Assim nossa equipe personaliza o atendimento e torna mais especial  
> a entrega do presente."  
> — *Papai Noel Paulo Duarte* 🎅❤️

Agradecemos pela confiança!  
Boas festas! 🎄✨
"""

    msg.set_content(corpo)

    # Anexar KR Code
    with open(anexo_krcode, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="image",
            subtype="jpeg",
            filename="KRCode_Pix.jpg"
        )

    # Anexar Foto do Noel
    with open(anexo_noel, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="image",
            subtype="png",
            filename="Papai_Noel.png"
        )

    # Envio de e-mail via Gmail
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ORIGEM, SENHA_EMAIL)
        smtp.send_message(msg)


# ------------------------------------
#  ROTAS DA APLICAÇÃO
# ------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/horarios_indisponiveis", methods=["POST"])
def horarios_indisponiveis():
    data_solicitada = request.form.get("data")
    ocupados = [r["horario"] for r in reservas if r["data"] == data_solicitada]

    return jsonify({
        "ocupados": ocupados,
        "horarios_disponiveis": HORARIOS
    })


@app.route("/enviar", methods=["POST"])
def enviar():
    dados = {
        "data": request.form["data"],
        "horario": request.form["horario"],
        "responsavel": request.form["responsavel"],
        "numero_criancas": int(request.form["numero_criancas"]),
        "email": request.form["email"],
        "telefone": request.form.get("telefone", ""),
        "observacoes": request.form.get("observacoes", ""),
        "endereco": request.form.get("endereco", ""),
        "bairro": request.form.get("bairro", ""),
        "cidade": request.form.get("cidade", ""),
        "status_pagamento": "Pendente",  # Sempre inicia pendente
    }

    # Calcular valor total
    dados["valor_total"] = dados["numero_criancas"] * VALOR_POR_CRIANCA

    # Formatar data para texto
    data_obj = datetime.strptime(dados["data"], "%Y-%m-%d")
    dados["data_formatada"] = data_obj.strftime("%d/%m/%Y")

    # Registrar no sistema (memória)
    reservas.append(dados)

    # Anexos
    caminho_krcode = os.path.join("static", "KrCode pix Paulo.jpg")
    caminho_noel = os.path.join("static", "noel.png")

    # Enviar o e-mail
    enviar_email_confirmacao(dados, caminho_krcode, caminho_noel)

    return render_template("index.html", mensagem="Reserva enviada com sucesso! ✔")


# -------------------------
#  EXECUTAR SERVIDOR
# -------------------------

if __name__ == "__main__":
    app.run(debug=True)


