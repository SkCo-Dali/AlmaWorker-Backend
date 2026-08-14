# AlmaWorker-Backend

Azure Function (Python) con los **timers del Motor de Suscripción de Alma**.
Patrón DaliWorker: la Function es un disparador delgado que llama endpoints
internos de `alma-backend` (`/internal/*`) — toda la lógica de negocio vive
en el backend.

```
AlmaWorker (timer cada 5 min, VNet integration)
   │  POST /internal/suscripcion/worker/tick  (X-Worker-Api-Key)
   ▼
alma-backend ──► pharos-bridge (COAZIR01/04) ──► Sigscg.TrkApplications (bandeja)
   │                                        └──► BD Pharos (declaraciones pre-emisión)
   ▼                                        └──► chankla (datos del asegurado)
BD Alma (suscripcion.AfiliacionesCotizaciones / Solicitudes / SolicitudDeclaraciones)
```

## Infraestructura (ya creada vía az, 2026-08-14)

| Ambiente | Function App | Plan | Storage | Backend destino |
|---|---|---|---|---|
| Dev | `skcoAlmaWorkerDev` (RG-SkCoAlma-Dev, sub Dev/Test Data Co) | AlmaPlanDev (compartido con skcoAlmaDev) | skcoalmaworkerdev | skcoAlmaDev |
| Prd | `skcoAlmaWorkerPrd` (RG-SkCoAlma-Prd, sub Produccion Data Co) | AlmaPlanPrd | skcoalmaworkerprd | skcoAlmaPrd |

Ambas con VNet integration (misma subnet del backend), Always On y App Insights.

## App Settings requeridos (Function App)

- `ALMA_API_BASE_URL` — URL del backend del ambiente.
- `WORKER_API_KEY` — la misma configurada en el App Service del backend
  (generar: `python -c "import secrets; print(secrets.token_urlsafe(48))"`).
- `AFILIACIONES_MAX_PAGINAS` (default 10), `AFILIACIONES_TOP` (default 500).
- `WEBSITE_TIME_ZONE=America/Bogota` (los CRON corren en hora local).

## CI/CD

`develop` → skcoAlmaWorkerDev, `main` → skcoAlmaWorkerPrd (GitHub Environments
`Development`/`Production` con secret `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` y
var `AZURE_FUNCTIONAPP_NAME`). El workflow instala dependencias en
`.python_packages` (modelo estándar de Functions Python).

## Desarrollo local

```powershell
copy local.settings.json.example local.settings.json   # completar valores
func start
```
