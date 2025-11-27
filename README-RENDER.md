# BookBazaar — Render Deploy

## Local
- Create 'bookbazaar/backend/.env' (copy from '.env.example')
- Use: DATABASE_URL=sqlite:///db.sqlite3
- Run:
  cd bookbazaar/backend
  python manage.py migrate
  python manage.py runserver

## Render (Web Service)
Build:
  pip install -r requirements.txt
  python bookbazaar/backend/manage.py collectstatic --noinput

Start:
  gunicorn bookbazaar.wsgi --workers 3 --chdir bookbazaar/backend --bind 0.0.0.0:\

Env Vars:
  SECRET_KEY=<random>
  DEBUG=0
  ALLOWED_HOSTS=bookbazaar-0jew.onrender.com,localhost,127.0.0.1
  CSRF_TRUSTED_ORIGINS=https://bookbazaar-0jew.onrender.com
  DATABASE_URL=mysql://USER:PASSWORD@HOST:3306/DBNAME   (URL-encode @ as %40)
  RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET (optional)

After first deploy, open Render Shell:
  python bookbazaar/backend/manage.py migrate
  python bookbazaar/backend/manage.py createsuperuser
