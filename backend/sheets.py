import gspread
from oauth2client.service_account import ServiceAccountCredentials

from config import SPREADSHEET_NAME

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 🔐 USA ARQUIVO (MELHOR PRA DEPLOY)
creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credenciais.json",
    scope
)

client = gspread.authorize(creds)

sheet = client.open(SPREADSHEET_NAME).sheet1


def get_all_data():
    return sheet.get_all_values()


def update_cell(linha, coluna, valor):
    sheet.update_cell(linha, coluna, valor)


def get_cell(linha, coluna):
    return sheet.cell(linha, coluna).value