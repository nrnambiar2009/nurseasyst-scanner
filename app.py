from flask import Flask, request, jsonify
from PIL import Image
from pyzbar.pyzbar import decode as decode_1d
from pylibdmtx.pylibdmtx import decode as decode_dm
import io
import urllib.request
import json

app = Flask(__name__)

def resize_image(img, max_size=1200):
    ratio = min(max_size / img.width, max_size / img.height)
    if ratio < 1:
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    return img

def lookup_product_name(gtin):
    if not gtin or len(gtin) < 12:
        return None
    # Strip first and last digit to get inner digits
    inner = gtin[1:-1]
    # Try multiple NDC split positions
    candidates = [
        f"{inner[1:6]}-{inner[6:10]}",   # 5-4
        f"{inner[2:7]}-{inner[7:11]}",   # 5-4 offset
        f"{inner[1:7]}-{inner[7:10]}",   # 6-3
        f"{inner[2:6]}-{inner[6:10]}",   # 4-4
    ]
    for ndc in candidates:
        try:
            url = f"https://api.fda.gov/drug/ndc.json?search=product_ndc:%22{ndc}%22&limit=1"
            with urllib.request.urlopen(url, timeout=5) as res:
                data = json.loads(res.read())
                item = data.get("results", [{}])[0]
                if item:
                    name = item.get("brand_name") or item.get("generic_name")
                    if name:
                        return name
        except Exception:
            continue
    return None

@app.route("/scan", methods=["POST"])
def scan():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]
    img_bytes = file.read()

    try:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img = resize_image(img)
    except Exception as e:
        return jsonify({"error": f"Invalid image: {str(e)}"}), 400

    # Try DataMatrix first
    dm_results = decode_dm(img)
    if dm_results:
        text = dm_results[0].data.decode("utf-8", errors="replace")
        return jsonify({"text": text, "type": "datamatrix"})

    # Try 1D barcodes
    results_1d = decode_1d(img)
    if results_1d:
        text = results_1d[0].data.decode("utf-8", errors="replace")
        return jsonify({"text": text, "type": results_1d[0].type})

    return jsonify({"error": "No barcode found"}), 404

@app.route("/lookup", methods=["GET"])
def lookup():
    gtin = request.args.get("gtin", "")
    name = lookup_product_name(gtin)
    if name:
        return jsonify({"productName": name})
    return jsonify({"productName": None}), 404

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)