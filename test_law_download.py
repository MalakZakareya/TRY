from services.regulation_importer import (
    download_official_law,
    extract_pdf_text,
)


LAW_URL = "https://www.lloc.gov.bh/PDF/K3612.pdf"


print("1. Downloading official Bahrain Labour Law...")

pdf_content = download_official_law(LAW_URL)

print("2. PDF downloaded successfully.")
print("PDF size:", len(pdf_content), "bytes")


print("\n3. Extracting text...")

text = extract_pdf_text(pdf_content)

print("4. Text extracted successfully.")
print("Characters:", len(text))


print("\n========== TEXT PREVIEW ==========\n")

print(text[:3000])

print("\n========== END PREVIEW ==========")