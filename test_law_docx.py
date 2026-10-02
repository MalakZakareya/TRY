import requests
from io import BytesIO
from docx import Document


LAW_URL = "https://www.lloc.gov.bh/FullAr/K3612.docx"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    )
}


print("1. Downloading consolidated law...")

response = requests.get(
    LAW_URL,
    headers=headers,
    timeout=30
)

response.raise_for_status()

print("2. Law downloaded successfully.")
print("File size:", len(response.content), "bytes")


print("\n3. Reading DOCX...")

document = Document(
    BytesIO(response.content)
)

paragraphs: list[str] = []

for paragraph in document.paragraphs:

    text = paragraph.text.strip()

    if text:
        paragraphs.append(text)


law_text = "\n".join(paragraphs)


print("4. Text extracted successfully.")
print("Characters:", len(law_text))


print("\n========== TEXT PREVIEW ==========\n")

print(law_text[:5000])

print("\n========== END PREVIEW ==========")