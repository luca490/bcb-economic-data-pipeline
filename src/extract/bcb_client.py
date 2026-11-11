import time
import requests

MAX_TENTATIVAS = 3
ESPERA_SEGUNDOS = 2

def fetch_series(series_code, start_date, end_date):
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_code}/dados"
    params = {"formato": "json", "dataInicial": start_date, "dataFinal": end_date}

    for tentativa in range(MAX_TENTATIVAS):
        try:
            resposta = requests.get(url, params=params, timeout=30)
            resposta.raise_for_status()
            return resposta.json()

        except requests.exceptions.RequestException:
            if tentativa == MAX_TENTATIVAS - 1:
                raise

            print(f"Falha na tentativa {tentativa + 1}. Tentando novamente...")
            time.sleep(ESPERA_SEGUNDOS)