import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(
    "service_account.json",
    scopes=SCOPES
)

client = gspread.authorize(creds)

sheet = client.open_by_key("12C4VM7yU4i1TUrxA0tpPp1zfpDvvoSAeBGkTgZa1x6E")
worksheet = sheet.sheet1

worksheet.update("A1", "GitHub test werkt")

print("Sheet update gelukt")
