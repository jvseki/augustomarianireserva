import gspread
import json
import os
from oauth2client.service_account import ServiceAccountCredentials
from config import SPREADSHEET_NAME

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 🔥 pega credenciais do Render
info = json.loads(os.environ["GOOGLE_CREDENTIALS"])

creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
client = gspread.authorize(creds)

sheet = client.open(SPREADSHEET_NAME).sheet1


def get_all_data():
    return sheet.get_all_values()


def get_cell(linha, coluna):
    return sheet.cell(linha, coluna).value


def update_cell(linha, coluna, valor):
    sheet.update_cell(linha, coluna, valor)