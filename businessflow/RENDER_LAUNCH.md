# BusinessFlow full-stack demo: Render launch

The frontend is already hosted at https://businessflow-crm.pages.dev. This repository now contains a root-level `render.yaml` Blueprint to create a Python web service and a PostgreSQL database together.

## Activate the hosting resources (account owner action)

1. Sign in at https://dashboard.render.com/ and connect GitHub.
2. Choose **New > Blueprint**, select `disCrybee/HTMLProjects` and branch `main`.
3. Keep the **Blueprint path** as `render.yaml`, review any displayed costs and permissions, then approve creation.
4. Wait for the database and `businessflow-api` web service to report healthy.
5. Copy the API's **HTTPS URL** from Render.
6. Open https://businessflow-crm.pages.dev/cloud.html. Paste **only your own** API URL. Create a demo account with a unique password (12+ characters), then sign in.
7. Test clients, deals and tasks, refresh the page, and check data persists.

**Don't paste credentials or connection strings in chats or source files.** Render injects the PostgreSQL URL and signing secret as server-side environment variables.

## Important limits

- The Render Free Postgres database **expires after 30 days**. This is a test environment only; do not enter real customer data.
- The free web service can spin down when idle.
- This prototype **lacks production-grade abuse protection, account recovery, session revocation and versioned migrations**. Do not treat it as an operational SaaS product.
- Cloudflare Pages only hosts the frontend; the Python API must be deployed separately.
- GitHub commits cannot provision resources inside Render without the account owner approving a Blueprint or providing an authorized hosting connection.

## Verify

- GET `https://<your-service>.onrender.com/health` returns `{"status":"ok"}`.
- `/auth/register`, `/auth/login` and `/api/*` require a running backend.
- Confirm network calls succeed from the browser and there are no CORS errors.
- Check latest GitHub Actions tests before calling deployment verified.

