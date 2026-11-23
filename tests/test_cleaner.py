import pandas as pd

from src.transform.cleaner import clean_series

INGESTED = "2026-11-23T17:17:58+00:00"


def test_data_e_lida_com_dia_primeiro():
    df = pd.DataFrame({"data": ["02/01/2025"], "valor": ["0.045513"]})
    r = clean_series(df, 11, INGESTED)
    assert r["data"].iloc[0] == pd.Timestamp(2025, 1, 2)  # 2 de janeiro, nao 1 de fevereiro


def test_valor_vira_numero_com_ponto_ou_virgula():
    df = pd.DataFrame({"data": ["02/01/2025", "03/01/2025"], "valor": ["0.045513", "0,041065"]})
    r = clean_series(df, 11, INGESTED)
    assert r["valor"].tolist() == [0.045513, 0.041065]


def test_linhas_invalidas_sao_descartadas():
    df = pd.DataFrame({
        "data": ["02/01/2025", "xx/yy/zzzz", "04/01/2025"],
        "valor": ["0.1", "0.2", "abc"],
    })
    r = clean_series(df, 11, INGESTED)
    assert len(r) == 1


def test_duplicatas_mantem_a_ultima():
    df = pd.DataFrame({"data": ["02/01/2025", "02/01/2025"], "valor": ["0.1", "0.9"]})
    r = clean_series(df, 11, INGESTED)
    assert len(r) == 1
    assert r["valor"].iloc[0] == 0.9


def test_resultado_vem_ordenado_por_data():
    df = pd.DataFrame({"data": ["05/01/2025", "02/01/2025"], "valor": ["0.2", "0.1"]})
    r = clean_series(df, 11, INGESTED)
    assert r["data"].is_monotonic_increasing