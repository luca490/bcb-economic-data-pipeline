import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from src.extract.bcb_client import fetch_series

logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")


def save_raw(series_code, start_date, end_date, dados, base_dir=RAW_DIR):
    """Grava o dado bruto em JSON, com metadados de ingestao."""
    agora = datetime.now(timezone.utc)
    pasta = Path(base_dir) / f"sgs_{series_code}" / f"ingestion_date={agora:%Y-%m-%d}"
    pasta.mkdir(parents=True, exist_ok=True)

    caminho = pasta / f"sgs_{series_code}_{agora:%Y%m%dT%H%M%S}Z.json"
    envelope = {
        "series_code": series_code,
        "start_date": start_date,
        "end_date": end_date,
        "ingested_at": agora.isoformat(),
        "record_count": len(dados),
        "data": dados,
    }

    temporario = caminho.with_suffix(".json.tmp")
    temporario.write_text(
        json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporario.replace(caminho)

    logger.info("Raw salvo em %s (%s registros)", caminho, len(dados))
    return caminho


def extract_to_raw(series_code, start_date, end_date):
    """Extrai da API e grava na camada raw. Devolve o caminho do arquivo."""
    dados = fetch_series(series_code, start_date, end_date)
    if not dados:
        logger.warning("Serie %s veio vazia no periodo informado", series_code)
    return save_raw(series_code, start_date, end_date, dados)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    print(extract_to_raw(11, "01/01/2025", "31/03/2025"))