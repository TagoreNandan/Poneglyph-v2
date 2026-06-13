from graph import fetch_report_images

print("Fetching images for Wano Kuni using updated pipeline...")
images = fetch_report_images("Wano Kuni")
print("\nFinal Image Results:")
for img in images:
    print(img)
