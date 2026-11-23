import json
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def load_raw(caminho):
    """Le um arquivo raw e devolve (metadados, DataFrame bruto)."""
    envelope = json.loads(Path(caminho).read_text(encoding="utf-8"))
    df = pd.DataFrame(envelope["data"])
    return envelope, df


def clean_series(df, series_code, ingested_at):
    """Converte tipos, remove duplicatas e acrescenta metadados."""
    limpo = df.copy()

    # 1. Data: dd/mm/aaaa -> datetime. dayfirst e formato explicito evitam o bug 02/01 vs 01/02
    limpo["data"] = pd.to_datetime(limpo["data"], format="%d/%m/%Y", errors="coerce")

    # 2. Valor: texto -> numero. Aceita virgula ou ponto decimal
    limpo["valor"] = pd.to_numeric(
        limpo["valor"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )

    # 3. Linhas com data ou valor invalidos viram NaT/NaN: contamos e descartamos
    invalidas = limpo["data"].isna() | limpo["valor"].isna()
    if invalidas.any():
        logger.warning("Serie %s: %s linhas invalidas descartadas", series_code, invalidas.sum())
    limpo = limpo[~invalidas]

    # 4. Duplicatas por data: mantem a ultima
    antes = len(limpo)
    limpo = limpo.drop_duplicates(subset="data", keep="last")
    if len(limpo) < antes:
        logger.warning("Serie %s: %s duplicatas removidas", series_code, antes - len(limpo))

    # 5. Metadados e ordenacao
    limpo["series_code"] = series_code
    limpo["ingested_at"] = pd.Timestamp(ingested_at)
    limpo = limpo.sort_values("data").reset_index(drop=True)

    return limpo[["series_code", "data", "valor", "ingested_at"]]


def transform_raw_file(caminho):
    envelope, df = load_raw(caminho)
    return clean_series(df, envelope["series_code"], envelope["ingested_at"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    arquivo = sorted(Path("data/raw").rglob("*.json"))[-1]
    resultado = transform_raw_file(arquivo)
    print(resultado.head())
    print(resultado.dtypes)
    print(len(resultado), "linhas")