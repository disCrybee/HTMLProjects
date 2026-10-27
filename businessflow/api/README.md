# BusinessFlow API

Backend for the BusinessFlow CRM portfolio project.

## Status

The API now implements password-based registration and login with short-lived signed bearer tokens. Client, deal and task records are scoped to the authenticated account. GitHub Actions runs integration tests.

**Not yet production-ready:** registration abuse controls, account recovery, session revocation, email verification, data migrations, audit logging and deployment configuration are still required. The public Cloudflare Pages demo is not connected to this API.

## Running

Python 3.12+:

```bash
pip install -r requirements.txt
export BUSINESSFLOW_SESSION_SECRET="replace-with-a-long-random-secret-at-least-32-characters"
uvicorn main:app --reload
```

PowerShell: `$env:BUSINESSFLOW_SESSION_SECRET="..."`

Use a cloud development environment if you do not want to download the project. Open `/docs` for interactive API documentation.

## Storage

`DATABASE_URL` defaults to `sqlite:///./businessflow.db`. For PostgreSQL install a compatible database driver and configure a `postgresql+psycopg://...` URL. `CORS_ORIGINS` accepts comma-separated allowed origins.

**Schema change:** owner IDs and the users table were added. SQLAlchemy `create_all()` does not migrate existing tables. Use a fresh development database for now; proper versioned migrations are required before deployment.

## Authentication

- `POST /auth/register`: email and password, minimum 12 characters
- `POST /auth/login`: return a 1-hour signed bearer access token
- `GET /auth/me`: return current account identity
- All `/api/*` endpoints require `Authorization: Bearer <token>`

Do not store tokens in public repositories or embed the session secret in frontend code.

## API

- `GET, POST /api/clients` and `DELETE /api/clients/{id}`
- `GET, POST /api/deals`, `PATCH, DELETE /api/deals/{id}`
- `GET, POST /api/tasks`, `PATCH, DELETE /api/tasks/{id}`
- `GET /api/metrics`

## Tests

```bash
pytest -q
```

GitHub Actions runs API tests on pushes and pull requests.
