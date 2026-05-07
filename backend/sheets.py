import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =========================
# 🔐 CONFIG GOOGLE
# =========================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# pega credenciais do Render
creds_json = os.environ.get("GOOGLE_CREDENTIALS")

if not creds_json:
    raise Exception("❌ GOOGLE_CREDENTIALS não configurado no Render")

try:
    creds_dict = json.loads(creds_json)
except Exception as e:
    raise Exception("❌ Erro ao ler JSON das credenciais: " + str(e))

# autenticação
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    creds_dict,
    scope
)

client = gspread.authorize(creds)

# =========================
# 📊 PLANILHA
# =========================

SHEET_NAME = "AGENDAMENTO NOTEBOOKS"

try:
    sheet = client.open(SHEET_NAME).sheet1
except Exception as e:
    raise Exception(f"❌ Erro ao abrir planilha: {e}")

# =========================
# 📌 FUNÇÕES
# =========================

def get_all_data():
    """Retorna todos os dados da planilha"""
    return sheet.get_all_records()


def get_cell(row, col):
    """Lê uma célula específica"""
    return sheet.cell(row, col).value


def update_cell(row, col, value):
    """Atualiza uma célula"""
    sheet.update_cell(row, col, value)


def clear_cell(row, col):
    """Limpa uma célula"""
    sheet.update_cell(row, col, "")