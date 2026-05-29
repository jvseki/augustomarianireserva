"""Envio de e-mails (SMTP) e templates de notificação."""
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

EMAIL_RE = re.compile(r"\[([^\]]+@[^\]]+)\]")

APP_URL = os.environ.get("APP_URL", "https://augustomarianireserva.vercel.app")

HORARIOS = {
    2: ("07:00", "07:50"),
    3: ("07:50", "08:40"),
    4: ("08:40", "09:30"),
    5: ("09:30", "09:50"),
    6: ("09:50", "10:40"),
    7: ("10:40", "11:30"),
    8: ("11:30", "12:20"),
    9: ("12:30", "13:20"),
    10: ("13:20", "14:10"),
    11: ("14:10", "15:00"),
    12: ("15:00", "15:20"),
    13: ("15:20", "16:10"),
    14: ("16:10", "17:00"),
    15: ("17:00", "17:50"),
}
DIAS_COL = {2: "Segunda", 3: "Terça", 4: "Quarta", 5: "Quinta", 6: "Sexta"}


def smtp_configurado():
    return bool(
        os.environ.get("SMTP_HOST")
        and os.environ.get("SMTP_USER")
        and os.environ.get("SMTP_PASSWORD")
    )


def enviar_email(destino, assunto, html, texto=None):
    destino = (destino or "").strip().lower()
    if not destino or "@" not in destino:
        print(f"[email] destino inválido: {destino!r}")
        return False
    if not smtp_configurado():
        print(f"[email] SMTP não configurado — pulando: {assunto} → {destino}")
        return False

    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    remetente = os.environ.get("EMAIL_FROM", user)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = remetente
    msg["To"] = destino
    corpo_texto = texto or re.sub(r"<[^>]+>", "", html)
    msg.attach(MIMEText(corpo_texto, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(host, port, timeout=25) as server:
            server.ehlo()
            if port == 587:
                server.starttls()
                server.ehlo()
            server.login(user, password)
            server.sendmail(remetente, [destino], msg.as_string())
        print(f"[email] enviado: {assunto} → {destino}")
        return True
    except Exception as e:
        print(f"[email] erro ao enviar para {destino}: {e}")
        return False


def formatar_slot(linha, coluna, cabecalho=None):
    dia = DIAS_COL.get(coluna)
    if not dia and cabecalho and coluna - 1 < len(cabecalho):
        dia = cabecalho[coluna - 1] or f"Dia {coluna}"
    dia = dia or f"Dia {coluna}"
    h = HORARIOS.get(linha)
    hora = f"{h[0]}–{h[1]}" if h else f"linha {linha}"
    return dia, hora


def coletar_emails_agenda(valores):
    emails = set()
    for row in valores or []:
        for cell in row:
            for m in EMAIL_RE.finditer(str(cell or "")):
                emails.add(m.group(1).lower().strip())
    return emails


def coletar_emails_espera(linhas, header):
    if not linhas or not header:
        return set()
    try:
        idx = header.index("email")
    except ValueError:
        return set()
    emails = set()
    for row in linhas[1:]:
        if idx < len(row):
            e = (row[idx] or "").strip().lower()
            if e and "@" in e:
                emails.add(e)
    return emails


def email_nova_semana(destino, semana_label):
    assunto = "📅 Nova semana liberada — Agendamento de Notebooks"
    html = f"""
    <p>Olá!</p>
    <p>A agenda do <strong>Laboratório de Informática</strong> para a semana de
    <strong>{semana_label}</strong> já está liberada para novos agendamentos.</p>
    <p>Você pode reservar tablets, notebooks e TV remota pelo sistema:</p>
    <p><a href="{APP_URL}">{APP_URL}</a></p>
    <p style="color:#666;font-size:12px;">Mensagem automática — toda sexta-feira às 18h a planilha
    passa a exibir a semana seguinte.</p>
    """
    return enviar_email(destino, assunto, html)


def email_promocao_fila(destino, nome, linha, coluna, equipamentos, cabecalho=None):
    dia, hora = formatar_slot(linha, coluna, cabecalho)
    primeiro = (nome or "Professor(a)").split()[0]
    assunto = f"✅ Sua vaga na lista de espera foi liberada — {dia} {hora}"
    html = f"""
    <p>Olá, <strong>{primeiro}</strong>!</p>
    <p>Boa notícia: abriu vaga para o equipamento que você pediu na lista de espera:</p>
    <ul>
      <li><strong>Dia:</strong> {dia}</li>
      <li><strong>Horário:</strong> {hora}</li>
      <li><strong>Equipamento:</strong> {equipamentos}</li>
    </ul>
    <p>Sua reserva já foi registrada na planilha. Acesse o sistema para conferir ou editar:</p>
    <p><a href="{APP_URL}">{APP_URL}</a></p>
    """
    return enviar_email(destino, assunto, html)


def proxima_segunda():
    """Data da segunda-feira da semana que abre após sexta 18h."""
    from datetime import timedelta

    hoje = datetime.now().date()
    ds = datetime.now().weekday()  # 0=seg … 4=sex
    if ds == 4:
        return hoje + timedelta(days=3)
    if ds == 5:
        return hoje + timedelta(days=2)
    if ds == 6:
        return hoje + timedelta(days=1)
    return hoje + timedelta(days=(7 - ds) % 7 or 7)


def label_proxima_semana():
    seg = proxima_segunda()
    from datetime import timedelta

    fim = seg + timedelta(days=4)
    return f"{seg.strftime('%d/%m')} a {fim.strftime('%d/%m/%Y')}"


def chave_semana_notificacao():
    iso = proxima_segunda().isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def agora_brasilia():
    """Horário de Brasília (para disparo automático na sexta 18h)."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/Sao_Paulo"))
    except Exception:
        from datetime import timedelta
        return datetime.utcnow() - timedelta(hours=3)


def deve_notificar_nova_semana_auto():
    """Sexta-feira a partir das 18h (Brasília) — sem Cron Job do Render."""
    agora = agora_brasilia()
    return agora.weekday() == 4 and agora.hour >= 18
