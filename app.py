import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, Response
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from functools import wraps
from dotenv import load_dotenv

# Carrega .env local (apenas para dev). Em Render as ENV vars já estarão setadas.
load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")

# ---------------------------
# CONFIGURAÇÃO VIA VARS DE AMBIENTE
# ---------------------------
EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "amagiadopapainoel1@gmail.com")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")  # obrigatória em produção
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")  # importante definir no Render

# ---------------------------
# PATHS DE ARQUIVOS
# ---------------------------
QR_CODE_PATH = os.path.join(app.root_path, "static", "KrCode pix Paulo.jpg")
NOEL_IMG_PATH = os.path.join(app.root_path, "static", "papai_noel.png")

# ---------------------------
# HORÁRIOS DO SISTEMA
# ---------------------------
# Horários reais (2 em 2 minutos)
INICIO = datetime(2025, 12, 24, 14, 0)
FIM = datetime(2025, 12, 25, 11, 0)
INTERVALO_MINUTOS = 2

# ---------------------------
# BANCO (SQLite)
# ---------------------------
DB_PATH = os.path.join(app.root_path, "reservas.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        responsavel TEXT,
        nome_crianca TEXT,
        email TEXT,
        telefone TEXT,
        data TEXT,
        horario_solicitado TEXT,
        horario_real TEXT,
        numero_criancas INTEGER,
        valor_total REAL,
        status TEXT,
        observacoes TEXT,
        criado_em TEXT
    );
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------------------
# HELPERS HORÁRIOS
# ---------------------------
def gerar_horarios_reais():
    horarios = []
    atual = INICIO
    delta = timedelta(minutes=INTERVALO_MINUTOS)
    while atual <= FIM:
        horarios.append(atual)
        atual += delta
    return horarios

HORARIOS_REAIS = gerar_horarios_reais()

def horarios_ocupados_set():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT horario_real FROM reservas WHERE horario_real IS NOT NULL")
    rows = cur.fetchall()
    conn.close()
    return set(r[0] for r in rows if r[0])

def encontrar_horario_real_posterior(ideal_dt):
    ocupados = horarios_ocupados_set()
    for h in HORARIOS_REAIS:
        if h >= ideal_dt:
            h_str = h.strftime("%Y-%m-%d %H:%M")
            if h_str not in ocupados:
                return h, h_str
    return None, None

# ---------------------------
# ENVIO DE E-MAIL (HTML com imagens inline)
# ---------------------------
def enviar_email_confirmacao(destinatario, dados, horario_final_dt):
    if not EMAIL_PASSWORD or not EMAIL_SENDER:
        app.logger.warning("EMAIL_SENDER ou EMAIL_PASSWORD não configurados. Ignorando envio de email.")
        return False

    msg = MIMEMultipart("related")
    msg["Subject"] = "🎅 Confirmação de Agendamento — Central de Distribuição de Presentes do Papai Noel"
    msg["From"] = EMAIL_SENDER
    msg["To"] = destinatario

    horario_formatado = horario_final_dt.strftime("%d/%m/%Y %H:%M")
    PIX_COPIA_COLA = (
        "00020126360014br.gov.bcb.pix0114+55419975658825204000053039865802BR5912PAULO_DUARTE"
        "6008Curitiba610981550-bc1qruqmcx20vwhv5dav2hlr4yg9n20kqz0fescezh"
    )

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background:#f7f7f7; padding:20px;">
      <div style="max-width:650px;margin:auto;background:#fff;padding:20px;border-radius:8px;">
        <h2 style="color:#b30000; text-align:center;">Central de Distribuição de Presentes do Papai Noel</h2>
        <p>Olá <strong>{dados['responsavel']}</strong>,</p>

        <p><b>Criança:</b> {dados['nome_crianca']}<br>
           <b>Horário solicitado:</b> {dados['horario_solicitado']}<br>
           <b>Horário confirmado:</b> <span style="color:#b30000;"><strong>{horario_formatado}</strong></span><br>
           <b>Valor:</b> R$ {float(dados['valor_total']):.2f}
        </p>

        <hr>
        <h3 style="color:#b30000;">Instruções de pagamento</h3>

        <p><b>PIX - Copia e Cola</b></p>
        <div style="background:#eee;padding:12px;border-radius:6px;word-break:break-all;">
            <code style="font-family:monospace;">{PIX_COPIA_COLA}</code>
        </div>

        <p><b>PIX - QR Code</b></p>
        <div style="text-align:center;">
          <img src='cid:qrcode' style='width:260px;border-radius:8px;border:2px solid #ddd;'/>
        </div>

        <hr>
        <p>Após o pagamento, envie o comprovante para:<br>
        <b>E-mail:</b> {EMAIL_SENDER}<br>
        <b>WhatsApp:</b> (41) 99756‑5882
        </p>

        <p style="text-align:center;margin-top:18px;">
          <img src='cid:noel' style='width:160px;'><br>
          <strong>Papai Noel — Paulo Duarte</strong>
        </p>
      </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html, "html"))

    # anexar imagens inline
    try:
        with open(QR_CODE_PATH, "rb") as f:
            img = MIMEImage(f.read())
            img.add_header("Content-ID", "<qrcode>")
            img.add_header("Content-Disposition", "inline")
            msg.attach(img)
    except Exception:
        app.logger.warning("QR code não encontrado: %s", QR_CODE_PATH)

    try:
        with open(NOEL_IMG_PATH, "rb") as f:
            img2 = MIMEImage(f.read())
            img2.add_header("Content-ID", "<noel>")
            img2.add_header("Content-Disposition", "inline")
            msg.attach(img2)
    except Exception:
        app.logger.warning("Noel image not found: %s", NOEL_IMG_PATH)

    # enviar via SMTP
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=60)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        app.logger.error("Erro ao enviar email: %s", e)
        return False

# ---------------------------
# ROTAS (formulário + envio)
# ---------------------------
@app.route("/", methods=["GET"])
def index():
    # horários de exibição (30 em 30 minutos) — front envia em formato "%Y-%m-%d %H:%M"
    display = []
    atual = INICIO
    while atual <= FIM:
        display.append(atual.strftime("%Y-%m-%d %H:%M"))
        atual += timedelta(minutes=30)
    return render_template("index.html", horarios=display)

@app.route("/enviar", methods=["POST"])
def receber_form():
    # Recebe dados do front
    responsavel = request.form.get("responsavel", "").strip()
    nome_crianca = request.form.get("nome_crianca", "").strip()
    email = request.form.get("email", "").strip()
    telefone = request.form.get("telefone", "").strip()
    data = request.form.get("data", "").strip()
    horario_solicitado = request.form.get("horario", "").strip()
    numero_criancas = int(request.form.get("numero_criancas") or 1)
    valor_total = float(request.form.get("valor_total") or 0.0)
    observacoes = request.form.get("observacoes", "").strip()

    # parse horario
    try:
        ideal_dt = datetime.strptime(horario_solicitado, "%Y-%m-%d %H:%M")
    except Exception:
        return "Horário inválido", 400

    horario_real_dt, horario_real_str = encontrar_horario_real_posterior(ideal_dt)
    if horario_real_dt is None:
        return "Sem horários disponíveis", 400

    criado_em = datetime.utcnow().isoformat()

    # Salvar no DB
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO reservas
        (responsavel, nome_crianca, email, telefone, data, horario_solicitado, horario_real, numero_criancas, valor_total, status, observacoes, criado_em)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (responsavel, nome_crianca, email, telefone, data, horario_solicitado, horario_real_str, numero_criancas, valor_total, "Pendente", observacoes, criado_em))
    conn.commit()
    conn.close()

    # enviar email de confirmação (assíncrono seria melhor, mas enviamos direto aqui)
    dados = {
        "responsavel": responsavel,
        "nome_crianca": nome_crianca,
        "horario_solicitado": horario_solicitado,
        "valor_total": valor_total
    }
    enviar_email_confirmacao(email, dados, horario_real_dt)

    return redirect(url_for("sucesso"))

@app.route("/sucesso")
def sucesso():
    return render_template("sucesso.html")

# ---------------------------
# AUTENTICAÇÃO BÁSICA (admin)
# ---------------------------
def check_auth(username, password):
    if ADMIN_PASSWORD is None:
        return False
    return username == ADMIN_USER and password == ADMIN_PASSWORD

def authenticate():
    return Response('Login required', 401, {'WWW-Authenticate': 'Basic realm="Admin Area"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# ---------------------------
# PAINEL ADMIN
# ---------------------------
@app.route("/admin")
@requires_auth
def admin():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, responsavel, nome_crianca, email, telefone, data, horario_solicitado, horario_real, numero_criancas, valor_total, status, observacoes, criado_em FROM reservas ORDER BY criado_em DESC")
    rows = cur.fetchall()
    conn.close()
    return render_template("admin.html", reservas=rows)

@app.route("/admin/mark_paid/<int:reserva_id>", methods=["POST"])
@requires_auth
def mark_paid(reserva_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE reservas SET status = ? WHERE id = ?", ("Pago", reserva_id))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

# ---------------------------
# RODAR APP
# ---------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)


