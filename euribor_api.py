import requests
from config import API_NINJAS_KEY

api_url = 'https://api.api-ninjas.com/v1/euribor'
api_key = API_NINJAS_KEY

def get_euribor_rates():
    headers = {"X-Api-Key": api_key}
    response = requests.get(api_url, headers=headers, timeout=5)
    if response.status_code == 200:
        data = response.json()
        # Extrai os valores para os prazos pretendidos
        euribor = {}
        for item in data:
            if item["name"] == "Euribor - 3 months":
                euribor["3m"] = (item["rate_pct"], item["last_updated"])
            elif item["name"] == "Euribor - 6 months":
                euribor["6m"] = (item["rate_pct"], item["last_updated"])
            elif item["name"] == "Euribor - 12 months":
                euribor["12m"] = (item["rate_pct"], item["last_updated"])
        return euribor
    else:
        print("Erro ao obter Euribor:", response.status_code, response.text)
        return None