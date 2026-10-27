# BusinessFlow API

REST API foundation for the BusinessFlow CRM demo.

## Run locally or in a cloud development environment

Python 3.11+:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

API docs: http://127.0.0.1:8000/docs

Run tests:

```bash
pytest -q
```

## Configuration

- `DATABASE_URL` defaults to local SQLite (`sqlite:///./businessflow.db`). For PostgreSQL, install a compatible driver (such as `psycopg[binary]`) and use `postgresql+psycopg://...`.
- `CORS_ORIGINS` is a comma-separated list of allowed frontend origins.

## Endpoints

- `GET /health`
- `GET, POST /api/clients`, `DELETE /api/clients/{id}`
- `GET, POST /api/deals`, `PATCH, DELETE /api/deals/{id}`
- `GET, POST /api/tasks`, `PATCH, DELETE /api/tasks/{id}`
- `GET /api/metrics`

## Development status

This is an **unreleased backend foundation**. The public Cloudflare Pages site continues to use browser localStorage; it is not yet connected to these endpoints. **Do not deploy the API publicly as a multi-user CRM** until authentication, per-user access controls, rate limiting, migrations, and production configuration are implemented. Sample accounts or login claims are not implemented.
