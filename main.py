import gspread
from google.oauth2.service_account import Credentials
from config import SHEET_KEY

def connect_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file("service_account.json", scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_KEY).sheet1
    return sheet

def write_sample_data(sheet):
    # test of alles werkt
    data = [
        ["Keyword", "Ad ID", "Views", "Engagement Score"],
        ["kitchen gadget", "12345", 50000, 0.25],
        ["car accessory", "67890", 80000, 0.40]
    ]
    sheet.clear()
    sheet.update("A1", data)

def main():
    sheet = connect_sheet()
    write_sample_data(sheet)
    print("Data succesvol naar Sheet geschreven!")

if __name__ == "__main__":
    main()