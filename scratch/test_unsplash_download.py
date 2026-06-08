import requests
import urllib3
from io import BytesIO
from PIL import Image as PILImage

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
url = "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=600&auto=format&fit=crop"
print(f"Downloading: {url}")
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
try:
    resp = requests.get(url, headers=headers, verify=False, timeout=8)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        pil_img = PILImage.open(BytesIO(resp.content))
        print(f"Success! Image loaded. Format: {pil_img.format}, Size: {pil_img.size}, Mode: {pil_img.mode}")
    else:
        print(f"Failed with status: {resp.status_code}")
except Exception as e:
    print(f"Error: {e}")
