from services.regulation_importer import add_regulation


regulation = {
    "id": "BH-LABOUR-36-2012-ARTICLE-39-P2",
    "title": "Labour Law for the Private Sector",
    "law_number": "36",
    "year": 2012,
    "category": "labour",
    "article": "39 - Paragraph 2",
    "text": (
        "ويُحظر التمييز في الأجور بين العمال والعاملات "
        "في العمل ذي القيمة المتساوية."
    ),
    "source_url": "https://www.lloc.gov.bh/Legislation/HTM/L1621",
    "source_type": "official",
    "effective_status": "in_force",
    "notes": (
        "Added by Legislative Decree No. 16 of 2021 "
        "amending Law No. 36 of 2012."
    )
}
add_regulation(regulation)
print("Regulation imported successfully.")
