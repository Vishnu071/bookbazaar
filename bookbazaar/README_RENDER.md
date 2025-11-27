# Deploying BookBazaar to Render (no Docker)

This guide shows a minimal set of steps to deploy the Django `BookBazaar` project to Render.com without Docker.

Prereqs on Render

- Create a Render account and a new Web Service (Static or Private services are not used here).
- Optionally create a managed Postgres database on Render and copy its `DATABASE_URL`.

Files added

- `Procfile` — tells Render how to run the app: `web: gunicorn --chdir backend bookbazaar.wsgi:application --log-file -`
- `render.yaml` — example Render manifest you can adapt and import into Render.

Render Service settings (recommended)

- Environment: `Python 3` or `Python` (Render auto-detects from `requirements.txt`).
- Build command: `pip install -r requirements.txt`
- Start command: Use the `Procfile` or set:
  `gunicorn --chdir backend bookbazaar.wsgi:application --log-file -`

Environment Variables to set on Render (minimum)

- `SECRET_KEY` : a long, random string
- `DEBUG` : `false`
- `ALLOWED_HOSTS` : your Render service domain (e.g. `bookbazaar-web.onrender.com`) or comma-separated list
- `DATABASE_URL` : (e.g. `postgres://...`) — required if you don't want to use local sqlite
- `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` : if using Razorpay payments
- `REDIS_URL` : if running Celery or caching

MySQL on Render (recommended)

- Create a Managed Database on Render and choose **MySQL** (or create a MySQL database externally).
- Copy the `DATABASE_URL` connection string Render provides (it will look like `mysql://user:pass@host:3306/dbname`).
- In your Web Service environment variables add `DATABASE_URL` with that value.

GitHub Actions CI & Auto-deploy

- A GitHub Actions workflow `/.github/workflows/render_deploy.yml` is included. It runs a lightweight Django check and then triggers a Render deploy using the Render API.
- You must add these repository secrets in GitHub settings:
  - `RENDER_API_KEY` — create a Render API key on Render dashboard (Account -> API Keys).
  - `RENDER_SERVICE_ID` — your Render Web Service ID (from the service URL or Render dashboard).
- The workflow triggers on pushes to `main` and will skip the deploy step if the secrets are not set.

Build hooks (recommended)

- Add a `Post-Deploy` hook that runs migrations and static collection (or run them manually from shell):

  ```bash
  # Run these commands in the Render shell after deploy (or add to a deploy hook)
  python backend/manage.py migrate --noinput
  python backend/manage.py collectstatic --noinput
  ```

Optional: render.yaml

- `render.yaml` is provided as an example manifest. You can import it into Render or use it as documentation.

Render UI steps (detailed)

- 1. Create a new **Web Service** on Render and connect your Git repository (choose the `bookbazaar` repo and branch `main`).
- 2. Use the `render.yaml` manifest or set these values in the UI:
  - **Environment**: Python
  - **Build Command**: `pip install -r requirements.txt`
  - **Start Command**: Use the `Procfile` or `gunicorn --chdir backend bookbazaar.wsgi:application --log-file -`
  - **Auto-Deploy**: enable if you want deploys on push
- 3. Create a Managed Database on Render (choose **MySQL**). Copy the provided connection string and set it as the `DATABASE_URL` environment variable in your Web Service.
- 4. (Optional) Create a Worker service on Render using the `render.yaml` worker entry or create a new Worker via the UI and set its start command to:
     `celery -A backend worker -l info`
- 5. Add environment variables in the Web Service settings:
  - `SECRET_KEY` — a secure random string
  - `DEBUG=false`
  - `ALLOWED_HOSTS` — your Render domain
  - `DATABASE_URL` — the MySQL connection string
  - `REDIS_URL` — if using Celery/Redis (also set for the Worker)
  - `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` — if using Razorpay
- 6. Deploy the service (manual or via the GH Action). After the service builds, open the Render shell (Dashboard → Shell) and run:

  ```bash
  # Run inside the Render shell for your Web Service
  python backend/manage.py migrate --noinput
  python backend/manage.py collectstatic --noinput
  ```

CI / Auto-deploy notes

- The included GitHub Action `/.github/workflows/render_deploy.yml` runs Django checks on `main` and triggers a Render deploy via the Render API. To enable full auto-deploy, add these GitHub secrets to your repository:
  - `RENDER_API_KEY` — create this in Render (Account → API Keys)
  - `RENDER_SERVICE_ID` — your Web Service ID from Render (found on the service details page)
- After adding the secrets, pushes to `main` will run checks and trigger a deploy (the workflow will skip deploy if the secrets are not present).

Rollback / run migrations in CI

- For safety, we recommend running migrations manually from the Render Shell on the first deploy. If you prefer to automate migrations, add a small step in your CI pipeline (careful: running migrations in parallel with multiple deploys can be risky):

  ```yaml
  # Example snippet: run as a CI step after deploy is triggered and before traffic switch
  - name: Run migrations on Render
    env:
      RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
      RENDER_SERVICE_ID: ${{ secrets.RENDER_SERVICE_ID }}
    run: |
      # Use Render shell api or add a deploy hook that runs migrations on the server
      echo "Run migrations manually in Render shell or add a safe deploy hook."
  ```

Local verification steps (PowerShell)

```powershell
# from repository root (d:\project\bookbazaar)
python -m venv .venv
.\.venv\Scripts\Activate
python -m pip install -r requirements.txt
cd backend
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver
```

Notes

- WhiteNoise is enabled in `settings.py` so static files are served from the app process. This is fine for small deployments. For better performance use a CDN.
- `dj-database-url` is included and the settings will use `DATABASE_URL` if present.
- For background workers (Celery), create a separate Worker service on Render and provide `REDIS_URL`.

If you'd like, I can:

- Generate a ready-to-use `render.yaml` that creates a managed Postgres and a web service (I will not run creation for you, only produce the manifest).
- Create a simple CI workflow (GitHub Actions) to auto-deploy to Render on push.
- Run a local Django `check` to surface immediate issues.

Tell me which of the above you'd like next.
