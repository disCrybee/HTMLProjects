# BusinessFlow API

REST API foundation for the BusinessFlow CRM demo.

## Run locally or in a cloud development environment

Python 3.11+:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Configure a private API key before starting the service:

```bash
export BUSINESSFLOW_API_KEY="replace-with-a-long-random-secret"
```

On Windows PowerShell, use `$env:BUSINESSFLOW_API_KEY="..."`.

Every `/api/*` endpoint requires `Authorization: Bearer <your-key>`. If no key is set, requests fail closed (503). **Never put this secret inside the public Pages frontend.** This key is only a temporary backend development guard, **not** a user login system.

API docs: http://127.0.0.1:8000/docs

Run tests:

```bash
pytest -q
```

## Configuration

- `DATABASE_URL` defaults to local SQLite (`sqlite:///./businessflow.db`). For PostgreSQL, install a compatible driver (such as `psycopg[binary]`) and use `postgresql+psycopg://...`.
- `CORS_ORIGINS` is a comma-separated list of allowed frontend origins.
- `BUSINESSFLOW_API_KEY` is a required private server-side secret.

## Endpoints

- `GET /health`
- `GET, POST /api/clients`, `DELETE /api/clients/{id}`
- `GET, POST /api/deals`, `PATCH, DELETE /api/deals/{id}`
- `GET, POST /api/tasks`, `PATCH, DELETE /api/tasks/{id}`
- `GET /api/metrics`

## Development status

This is an **unreleased backend foundation**. The public Cloudflare Pages site continues to use browser localStorage; it is not yet connected to these endpoints. **Do not deploy the API publicly as a multi-user CRM** until authentication, per-user access controls, rate limiting, migrations, and production configuration are implemented. Sample accounts or login claims are not implemented.
