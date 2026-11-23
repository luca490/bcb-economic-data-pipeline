import logging
import time

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
MAX_TENTATIVAS = 3
ESPERA_INICIAL_SEGUNDOS = 1
TIMEOUT_SEGUNDOS = 30


class ExtractionError(Exception):
    """Falha ao extrair dados da API do Banco Central."""


def _vale_tentar_de_novo(erro):
    """Erros temporarios (rede, 5xx) valem retry. Erros 4xx nao."""
    if isinstance(erro, (requests.exceptions.Timeout,
                         requests.exceptions.ConnectionError)):
        return True
    if isinstance(erro, requests.exceptions.HTTPError):
        return erro.response.status_code >= 500
    return False


def fetch_series(series_code, start_date, end_date):
    """Busca uma serie do SGS. Datas no formato dd/mm/aaaa."""
    url = BASE_URL.format(codigo=series_code)
    params = {"formato": "json", "dataInicial": start_date, "dataFinal": end_date}

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            resposta = requests.get(url, params=params, timeout=TIMEOUT_SEGUNDOS)
            resposta.raise_for_status()
            dados = resposta.json()
        except requests.exceptions.RequestException as erro:
            ultima = tentativa == MAX_TENTATIVAS
            if ultima or not _vale_tentar_de_novo(erro):
                logger.error("Falha definitiva na serie %s: %s", series_code, erro)
                raise ExtractionError(
                    f"Nao foi possivel extrair a serie {series_code}"
                ) from erro

            espera = ESPERA_INICIAL_SEGUNDOS * 2 ** (tentativa - 1)
            logger.warning(
                "Tentativa %s/%s falhou (%s). Nova tentativa em %ss",
                tentativa, MAX_TENTATIVAS, type(erro).__name__, espera,
            )
            time.sleep(espera)
            continue

        if not isinstance(dados, list):
            raise ExtractionError(f"Resposta inesperada para a serie {series_code}")

        logger.info("Serie %s: %s registros extraidos", series_code, len(dados))
        return dados