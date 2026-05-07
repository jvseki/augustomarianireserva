import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 🔥 Pega JSON da variável de ambiente
creds_json = os.environ.get("GOOGLE_CREDENTIALS")

if not creds_json:
    raise Exception("GOOGLE_CREDENTIALS não configurado")

creds_dict = json.loads(creds_json)

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    creds_dict,
    scope
)

client = gspread.authorize(creds)

SHEET_NAME = "AGENDAMENTO NOTEBOOKS"
sheet = client.open(SHEET_NAME).sheet1


def get_all_data():
    return sheet.get_all_records()


def get_cell(row, col):
    return sheet.cell(row, col).value


def update_cell(row, col, value):
    sheet.update_cell(row, col, value)


def clear_cell(row, col):
    sheet.update_cell(row, col, "")