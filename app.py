from flask import Flask, request, jsonify
from PIL import Image
from pyzbar.pyzbar import decode as decode_1d
from pylibdmtx.pylibdmtx import decode as decode_dm
import io

app = Flask(__name__)

@app.route("/scan", methods=["POST"])
def scan():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]
    img_bytes = file.read()

    try:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    except Exception as e:
        return jsonify({"error": f"Invalid image: {str(e)}"}), 400

    dm_results = decode_dm(img)
    if dm_results:
        text = dm_results[0].data.decode("utf-8", errors="replace")
        return jsonify({"text": text, "type": "datamatrix"})

    results_1d = decode_1d(img)
    if results_1d:
        text = results_1d[0].data.decode("utf-8", errors="replace")
        return jsonify({"text": text, "type": results_1d[0].type})

    return jsonify({"error": "No barcode found"}), 404

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)