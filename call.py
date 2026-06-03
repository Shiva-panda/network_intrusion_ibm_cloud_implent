import requests

IBM_API_KEY = "your_api_key_here"

response = requests.post(
    "https://iam.cloud.ibm.com/identity/token",
    data={
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": "0Dv5f2xVOtyRjND1Mgxceumkh3Ctk4Mabe96K24oKXhk"
    },
    headers={
        "Content-Type": "application/x-www-form-urlencoded"
    }
)

data = response.json()
print(data)