import requests
from bs4 import BeautifulSoup

URL = "https://ads.tiktok.com/business/creativecenter/topads/pc/en"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers)

print("Status code:", response.status_code)

soup = BeautifulSoup(response.text, "lxml")

title = soup.title.string if soup.title else "Geen title gevonden"

print("Page title:", title)
