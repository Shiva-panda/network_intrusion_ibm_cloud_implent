from flask import Flask, render_template, request, send_file
import pandas as pd
import requests
import os
from dotenv import load_dotenv
import io
import time

load_dotenv()

app = Flask(__name__)

# =========================
# IBM CONFIG
# =========================
IBM_API_KEY = os.getenv("IBM_API_KEY")

DEPLOYMENT_URL = "https://au-syd.ml.cloud.ibm.com/ml/v4/deployments/019e8d4a-cf53-75c1-b5e3-84c0ea576d8d/predictions?version=2021-05-01"

predicted_df = None

# =========================
# 41 FEATURES
# =========================
FIELDS = [
    "duration","protocol_type","service","flag","src_bytes","dst_bytes",
    "land","wrong_fragment","urgent","hot","num_failed_logins",
    "logged_in","num_compromised","root_shell","su_attempted","num_root",
    "num_file_creations","num_shells","num_access_files","num_outbound_cmds",
    "is_host_login","is_guest_login","count","srv_count","serror_rate",
    "srv_serror_rate","rerror_rate","srv_rerror_rate","same_srv_rate",
    "diff_srv_rate","srv_diff_host_rate","dst_host_count",
    "dst_host_srv_count","dst_host_same_srv_rate","dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate","dst_host_srv_diff_host_rate",
    "dst_host_serror_rate","dst_host_srv_serror_rate",
    "dst_host_rerror_rate","dst_host_srv_rerror_rate"
]

# =========================
# TOKEN
# =========================
def get_token():
    url = "https://iam.cloud.ibm.com/identity/token"

    response = requests.post(
        url,
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": IBM_API_KEY
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30
    )

    data = response.json()

    if "access_token" not in data:
        return None

    return data["access_token"]

# =========================
# HOME
# =========================
@app.route("/")
def home():
    return render_template("index.html")

# =========================
# PREDICT
# =========================
@app.route("/predict", methods=["POST"])
def predict():
    global predicted_df

    file = request.files.get("file")
    if not file:
        return "No file uploaded"

    df = pd.read_csv(file)

    missing = [c for c in FIELDS if c not in df.columns]
    if missing:
        return f"Missing columns: {missing}"

    df = df[FIELDS]

    # 🔥 SIMULATE LOADING (for popup UI)
    time.sleep(3)   # you can increase to 40 if needed

    token = get_token()
    if not token:
        return "IBM Auth Failed"

    payload = {
        "input_data": [{
            "fields": FIELDS,
            "values": df.values.tolist()
        }]
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(DEPLOYMENT_URL, json=payload, headers=headers, timeout=120)

    result = response.json()

    if "predictions" not in result:
        return str(result)

    predictions = result["predictions"][0]["values"]

    labels = []
    confidences = []

    for p in predictions:
        labels.append(str(p[0]).strip().lower())
        confidences.append(p[1] if len(p) > 1 else 0)

    df["label"] = labels
    df["confidence"] = confidences

    predicted_df = df

    results = df.to_dict(orient="records")

    return render_template(
        "index.html",
        results=results,
        download_ready=True
    )

# =========================
# DOWNLOAD
# =========================
@app.route("/download")
def download():
    global predicted_df

    if predicted_df is None:
        return "No data"

    output = io.StringIO()
    predicted_df.to_csv(output, index=False)
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="predicted.csv"
    )

# =========================
if __name__ == "__main__":
    app.run(debug=True)