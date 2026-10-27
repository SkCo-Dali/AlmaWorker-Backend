"""
AlmaWorker — timers de Alma (Suscripción, Buzón Inteligente y Monitor-IA).

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


@app.timer_trigger(
    schedule="0 */5 * * * *",   # cada 5 minutos
    arg_name="buzonTimer",
    run_on_startup=False,
    use_monitor=True,
)
def buzon_inteligente_tick(buzonTimer: func.TimerRequest) -> None:
    """Buzón Inteligente: ingesta (Graph delta) + clasificación IA + acciones de
    los buzones activos. La lógica vive en alma-backend (/internal/buzon-inteligente)."""
    logging.info("Buzon Inteligente Tick: starting...")
    payload = {"maxCorreos": int(os.getenv("BUZON_MAX_CORREOS", "25"))}
    try:
        resp = _post_internal("/internal/buzon-inteligente/worker/tick", payload)
        logging.info("Buzon Inteligente response: %s - %s",
                     resp.status_code, resp.text[:2000])
        resp.raise_for_status()
        logging.info("Buzon Inteligente Tick: OK")
    except Exception as e:
        logging.exception("Buzon Inteligente Tick: FAILED. Error: %s", e)


@app.timer_trigger(
    schedule="0 17 * * * *",   # cada hora, al minuto 17 (lejos de los ticks de 5 min)
    arg_name="buzonBasesTimer",
    run_on_startup=False,
    use_monitor=True,
)
def buzon_inteligente_bases(buzonBasesTimer: func.TimerRequest) -> None:
    """Buzón Inteligente 2.0: re-sincroniza desde SharePoint las bases de
    responsables que usan las reglas de asignación. La lógica vive en
    alma-backend (/internal/buzon-inteligente/worker/bases)."""
    logging.info("Buzon Inteligente Bases: starting...")
    try:
        resp = _post_internal("/internal/buzon-inteligente/worker/bases", {})
        logging.info("Buzon Inteligente Bases response: %s - %s",
                     resp.status_code, resp.text[:2000])
        resp.raise_for_status()
        logging.info("Buzon Inteligente Bases: OK")
    except Exception as e:
        logging.exception("Buzon Inteligente Bases: FAILED. Error: %s", e)


@app.timer_trigger(
    schedule="0 2-57/5 * * * *",   # cada 5 minutos, desfasado 2 min de los otros timers
    arg_name="monitorIaTimer",
    run_on_startup=False,
    use_monitor=True,
)
def monitor_ia_tick(monitorIaTimer: func.TimerRequest) -> None:
    """Monitor-IA: retoma las campañas de autoevaluación que el backend dejó a
    medias (reinicio) y trae de Genesys las notas pendientes. La lógica vive en
    alma-backend (/internal/monitor-ia). Sin credenciales de Genesys no hace nada."""
    logging.info("Monitor-IA Tick: starting...")
    try:
        resp = _post_internal("/internal/monitor-ia/worker/tick", {})
        logging.info("Monitor-IA response: %s - %s", resp.status_code, resp.text[:2000])
        resp.raise_for_status()
        logging.info("Monitor-IA Tick: OK")
    except Exception as e:
        logging.exception("Monitor-IA Tick: FAILED. Error: %s", e)
