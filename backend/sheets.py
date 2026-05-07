import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 🔥 Credenciais vindas do Render (variável de ambiente)
creds_json = os.environ.get("GOOGLE_CREDENTIALS")

if not creds_json:
    raise Exception("GOOGLE_CREDENTIALS não configurado no Render")

creds_dict = json.loads(creds_json)

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    creds_dict,
    scope
)

client = gspread.authorize(creds)

# =========================================
# 📌 SUA PLANILHA (USE O ID, NÃO O NOME)
# =========================================
SHEET_ID = "1uixhu6rN03HrMy-1ECf2U-Gr5bpKkbbiToiHGMOglk0"

sheet = client.open_by_key(SHEET_ID).sheet1


# =========================
# 📌 FUNÇÕES DO SISTEMA
# =========================

def get_all_data():
    return sheet.get_all_records()


def get_cell(row, col):
    return sheet.cell(row, col).value


def update_cell(row, col, value):
    sheet.update_cell(row, col, value)


def clear_cell(row, col):
    sheet.update_cell(row, col, "")