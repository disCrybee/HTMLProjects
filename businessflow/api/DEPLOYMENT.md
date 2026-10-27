# BusinessFlow deployment checklist

The public Pages dashboard and this API are separate deployments. The API is **not deployed by GitHub Actions**.

## Provision resources

1. Provision a managed PostgreSQL instance at a provider of your choice. Record its connection URL in the provider's private environment-variable settings; never commit it.
2. Provision a Python web service (e.g. Render) connected to this repository and set the root to `businessflow/api`.
3. Install requirements and launch `uvicorn main:app --host 0.0.0.0 --port $PORT`. Set `DATABASE_URL` with a PostgreSQL URL including `postgresql+psycopg://` when using psycopg.
4. Set `BUSINESSFLOW_SESSION_SECRET` to a randomly generated 32+ character secret, and restrict `CORS_ORIGINS` to the Pages origin.
5. Confirm `GET /health` and run registration/login/isolation smoke tests against a non-production test account.
6. For the new cloud-backed interface, open `businessflow/cloud.html` and enter the HTTPS origin of the API.

## Security notes

- Do not put the DB URL or session secret in client-side JavaScript or GitHub.
- The database currently uses `Base.metadata.create_all`. This is **not a migration tool**. Deploy only on a new database for this prototype. Introduce Alembic migrations before schema changes on live data.
- Rate limiting, email verification, recovery, token revocation and session hardening are still required for production.
- `render.yaml` is an optional blueprint for an account you control; it does not create resources automatically.
- A free service may sleep and can have uptime limitations. Database plans/prices vary.
