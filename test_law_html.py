import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


LAW_URL = "https://www.lloc.gov.bh/Legislation/id/K3612"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    )
}


response = requests.get(
    LAW_URL,
    headers=headers,
    timeout=30
)

response.raise_for_status()

soup = BeautifulSoup(
    response.text,
    "html.parser"
)


print("========== LEGISLATION LINKS ==========\n")


for link in soup.find_all("a"):

    text = link.get_text(
        " ",
        strip=True
    )

    href = link.get("href")

    # Make sure href is a string
    if not isinstance(href, str):
        continue

    if (
        "انظر كنص" in text
        or "التشريعات مع التعديلات" in text
    ):
        full_url = urljoin(
            LAW_URL,
            href
        )

        print("Name:", text)
        print("URL:", full_url)
        print("------------------------------")