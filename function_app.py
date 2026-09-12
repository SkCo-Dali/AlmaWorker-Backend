"""
AlmaWorker — timers del Motor de Suscripción de Alma.

Patrón DaliWorker: la Function es un disparador delgado; toda la lógica vive
en alma-backend detrás de /internal/* (así se prueba, versiona y despliega
junto al dominio). Auth: header X-Worker-Api-Key (App Setting WORKER_API_KEY,
la misma configurada en el App Service del backend).
"""

import logging
import os

import azure.functions as func
import requests

app = func.FunctionApp()


def _post_internal(endpoint_path: str, payload: dict, timeout: int = 300) -> requests.Response:
    base_url = os.environ["ALMA_API_BASE_URL"].rstrip("/")
    return requests.post(
        f"{base_url}{endpoint_path}",
        headers={
            "X-Worker-Api-Key": os.environ["WORKER_API_KEY"],
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=timeout,
    )


@app.timer_trigger(
    schedule="0 */5 * * * *",   # cada 5 minutos
    arg_name="afiliacionesTimer",
    run_on_startup=False,
    use_monitor=True,
)
def afiliaciones_sync_tick(afiliacionesTimer: func.TimerRequest) -> None:
    """Sincroniza la bandeja de afiliaciones (TrkApplications -> BD Alma)."""
    logging.info("Afiliaciones Sync Tick: starting...")
    payload = {
        "maxPaginas": int(os.getenv("AFILIACIONES_MAX_PAGINAS", "10")),
        "top": int(os.getenv("AFILIACIONES_TOP", "500")),
    }
    try:
        resp = _post_internal("/internal/suscripcion/worker/tick", payload)
        logging.info("Afiliaciones sync response: %s - %s",
                     resp.status_code, resp.text[:2000])
        resp.raise_for_status()
        logging.info("Afiliaciones Sync Tick: OK")
    except Exception as e:
        logging.exception("Afiliaciones Sync Tick: FAILED. Error: %s", e)
