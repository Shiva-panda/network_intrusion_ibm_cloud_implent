from flask import Flask, render_template, request
import pandas as pd
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# =========================
# IBM CONFIG (KEEP SECRET)
# =========================
IBM_API_KEY = os.getenv("IBM_API_KEY")

DEPLOYMENT_URL = "https://au-syd.ml.cloud.ibm.com/ml/v4/deployments/019e8d4a-cf53-75c1-b5e3-84c0ea576d8d/predictions?version=2021-05-01"

# =========================
# 41 FEATURES (KDD DATASET)
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
# GET IBM TOKEN
# =========================
def get_token():
    url = "https://iam.cloud.ibm.com/identity/token"

    response = requests.post(
        url,
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": IBM_API_KEY
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    data = response.json()

    if "access_token" not in data:
        raise Exception(f"IBM Auth Failed: {data}")

    return data["access_token"]

# =========================
# HOME PAGE
# =========================
@app.route("/")
def home():
    return render_template("index.html")

# =========================
# PREDICTION ROUTE
# =========================
@app.route("/predict", methods=["POST"])
def predict():
    try:
        file = request.files["file"]
        df = pd.read_csv(file)

        token = get_token()

        # Ensure correct columns exist
        missing = [c for c in FIELDS if c not in df.columns]
        if missing:
            return f"Missing columns: {missing}"

        df = df[FIELDS]

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

        response = requests.post(DEPLOYMENT_URL, json=payload, headers=headers, timeout=60)

        result = response.json()

        if "predictions" not in result:
            return f"IBM Error: {result}"

        predictions = result["predictions"][0]["values"]

        results = []
        for i, row in enumerate(predictions):
            results.append({
                "label": row[0],
                "confidence": row[1] if len(row) > 1 else "N/A",
                "protocol_type": df.iloc[i]["protocol_type"],
                "service": df.iloc[i]["service"],
                "src_bytes": df.iloc[i]["src_bytes"]
            })

        return render_template("index.html", results=results)

    except Exception as e:
        return f"Server Error: {str(e)}"

# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)