import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Escopos do Google Sheets
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Caminho correto do JSON dentro da pasta backend
base_dir = os.path.dirname(__file__)
cred_path = os.path.join(base_dir, "credenciais.json")

# Autenticação
creds = ServiceAccountCredentials.from_json_keyfile_name(
    cred_path,
    scope
)

client = gspread.authorize(creds)

# 🔥 TROQUE AQUI PELO NOME REAL DA SUA PLANILHA
SHEET_NAME = "AGENDAMENTO NOTEBOOKS"

sheet = client.open(SHEET_NAME).sheet1


# =========================
# 📌 FUNÇÕES DO SISTEMA
# =========================

def get_all_data():
    """Retorna todos os dados da planilha"""
    return sheet.get_all_records()


def get_cell(row, col):
    """Lê uma célula específica"""
    return sheet.cell(row, col).value


def update_cell(row, col, value):
    """
    Atualiza uma célula da planilha
    Exemplo: marcar professor ou reserva
    """
    sheet.update_cell(row, col, value)


def clear_cell(row, col):
    """Limpa uma célula"""
    sheet.update_cell(row, col, "")