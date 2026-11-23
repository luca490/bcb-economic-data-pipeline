import pytest
import requests

from src.extract import bcb_client
from src.extract.bcb_client import ExtractionError, fetch_series


class RespostaFalsa:
    def __init__(self, status=200, corpo=None):
        self.status_code = status
        self._corpo = [] if corpo is None else corpo

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(response=self)

    def json(self):
        return self._corpo


@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    """Os testes nao precisam esperar de verdade entre as tentativas."""
    monkeypatch.setattr(bcb_client.time, "sleep", lambda segundos: None)


def instalar_respostas(monkeypatch, respostas):
    """Troca requests.get por uma versao que devolve (ou levanta) cada item, em ordem."""
    chamadas = []

    def get_falso(*args, **kwargs):
        chamadas.append(1)
        item = respostas[len(chamadas) - 1]
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(bcb_client.requests, "get", get_falso)
    return chamadas


def test_sucesso_devolve_os_dados(monkeypatch):
    dados = [{"data": "02/01/2025", "valor": "0.045513"}]
    chamadas = instalar_respostas(monkeypatch, [RespostaFalsa(200, dados)])
    assert fetch_series(11, "01/01/2025", "31/03/2025") == dados
    assert len(chamadas) == 1


def test_404_nao_tenta_de_novo(monkeypatch):
    chamadas = instalar_respostas(monkeypatch, [RespostaFalsa(404)] * 3)
    with pytest.raises(ExtractionError):
        fetch_series(99999999, "01/01/2025", "31/03/2025")
    assert len(chamadas) == 1


def test_503_tenta_todas_as_vezes_e_falha(monkeypatch):
    chamadas = instalar_respostas(monkeypatch, [RespostaFalsa(503)] * 3)
    with pytest.raises(ExtractionError):
        fetch_series(11, "01/01/2025", "31/03/2025")
    assert len(chamadas) == bcb_client.MAX_TENTATIVAS


def test_timeout_seguido_de_sucesso_se_recupera(monkeypatch):
    dados = [{"data": "02/01/2025", "valor": "0.1"}]
    chamadas = instalar_respostas(
        monkeypatch, [requests.exceptions.Timeout(), RespostaFalsa(200, dados)]
    )
    assert fetch_series(11, "01/01/2025", "31/03/2025") == dados
    assert len(chamadas) == 2


def test_resposta_que_nao_e_lista_falha(monkeypatch):
    instalar_respostas(monkeypatch, [RespostaFalsa(200, {"erro": "algo"})])
    with pytest.raises(ExtractionError):
        fetch_series(11, "01/01/2025", "31/03/2025")