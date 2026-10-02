from services.regulation_importer import import_labour_law


print("Importing Bahrain Labour Law...")

count = import_labour_law()

print(
    f"Successfully imported {count} articles."
)