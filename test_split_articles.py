import re
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


# Download official consolidated law
response = requests.get(
    LAW_URL,
    headers=headers,
    timeout=30
)

response.raise_for_status()


# Read DOCX
document = Document(
    BytesIO(response.content)
)

paragraphs: list[str] = []

for paragraph in document.paragraphs:

    text = paragraph.text.strip()

    if text:
        paragraphs.append(text)


law_text = "\n".join(paragraphs)


# We only want the attached Labour Law itself.
# This avoids confusing:
# "المادة الأولى، الثانية..." from the promulgating law
# with Article (1), Article (2)... of the Labour Law.

marker = "قانون العمل في القطاع الأهلي"

first_position = law_text.find(marker)
second_position = law_text.find(
    marker,
    first_position + len(marker)
)

if second_position != -1:
    law_text = law_text[second_position:]


# Match:
# المادة (1)
# المادة (2)
# المادة (2) مكرراً
# etc.

pattern = re.compile(
    r"(?m)^المادة\s+\((\d+)\)"
    r"(?:\s+(مكرراً(?:\s+\d+)?))?\s*$"
)

matches = list(
    pattern.finditer(law_text)
)


print("========== ARTICLE SPLIT TEST ==========\n")

print("Articles found:", len(matches))


for index, match in enumerate(matches[:10]):

    article_number = match.group(1)
    repeated = match.group(2)

    if repeated:
        article_name = (
            f"{article_number} {repeated}"
        )
    else:
        article_name = article_number

    start = match.end()

    if index + 1 < len(matches):
        end = matches[index + 1].start()
    else:
        end = len(law_text)

    article_text = law_text[
        start:end
    ].strip()

    print("\n------------------------------")
    print("ARTICLE:", article_name)
    print("------------------------------")

    print(
        article_text[:500]
    )


print("\n========== END ==========")