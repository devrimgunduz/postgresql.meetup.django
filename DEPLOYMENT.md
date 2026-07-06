# postgresql.istanbul Django — Deployment Guide

## Stack

- Python 3.11+
- Django 4.2
- PostgreSQL (same DB as the PHP site, or fresh)
- Gunicorn (WSGI server)
- Apache (reverse proxy + static files)
- WhiteNoise (static file compression + cache headers)

---

## 1. System packages

```bash
# RHEL / AlmaLinux / Rocky Linux
dnf install python3.11 python3.11-pip python3.11-devel \
            mod_ssl mod_proxy

# Debian / Ubuntu
apt install python3.11 python3.11-venv libpq-dev \
            libapache2-mod-proxy-html
a2enmod proxy proxy_http ssl headers rewrite
```

---

## 2. Application setup

```bash
# Deploy location
mkdir -p /var/www/postgresql.istanbul/django
cp -r . /var/www/postgresql.istanbul/django/
cd /var/www/postgresql.istanbul/django

# Virtual environment
python3.11 -m venv /var/www/postgresql.istanbul/venv
source /var/www/postgresql.istanbul/venv/bin/activate
pip install -r requirements.txt

# Environment file
cp .env.example .env
# Edit .env — set SECRET_KEY, PGPASSWORD, etc.
nano .env

# Permissions
chown -R apache:apache /var/www/postgresql.istanbul/
chmod 750 /var/www/postgresql.istanbul/django/
chmod 640 /var/www/postgresql.istanbul/django/.env
```

---

## 3. Database & Django setup

```bash
source /var/www/postgresql.istanbul/venv/bin/activate
cd /var/www/postgresql.istanbul/django

# Run migrations (creates all tables)
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser for Django admin + custom panel
python manage.py createsuperuser

# Seed initial languages (run once)
python manage.py shell -c "
from meetups.models import Language
Language.objects.get_or_create(code='en', defaults={'label':'English','is_default':True,'sort_order':1})
Language.objects.get_or_create(code='tr', defaults={'label':'Türkçe','is_active':True,'sort_order':2})
print('Languages seeded.')
"
```

---

## 4. Gunicorn systemd service

```bash
mkdir -p /var/log/pgistanbul

cp deployment/pgistanbul.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable pgistanbul
systemctl start pgistanbul
systemctl status pgistanbul

# Check socket created:
ls -la /run/pgistanbul.sock
```

---

## 5. Apache

```bash
# RHEL/AlmaLinux:
cp deployment/apache.conf /etc/httpd/conf.d/postgresql.istanbul.conf
apachectl configtest && systemctl reload httpd

# Enable required modules if not already:
httpd -M | grep -E "proxy|ssl|headers"
```

---

## 6. TLS — Let's Encrypt

```bash
certbot --apache -d postgresql.istanbul -d www.postgresql.istanbul
```

---

## 7. Two admin interfaces

| URL | What it is |
|-----|-----------|
| `/django-admin/` | Django's built-in admin — full model access |
| `/admin-panel/` | Custom dark-themed admin panel |

Both use Django's auth system. The same superuser created in step 3 works for both.
Non-superusers need `is_staff=True` to access the custom panel.

---

## 8. Routine operations

```bash
# Restart after code changes
systemctl restart pgistanbul

# View logs
journalctl -u pgistanbul -f
tail -f /var/log/pgistanbul/error.log

# Run management commands
source /var/www/postgresql.istanbul/venv/bin/activate
cd /var/www/postgresql.istanbul/django
python manage.py <command>

# After adding new migrations:
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart pgistanbul
```

---

## 9. Adding languages

Go to `/admin-panel/languages/` and add any language with a code and label.
Or via Django admin at `/django-admin/meetups/language/`.

No migrations or code changes needed — the translation system is fully generic.

---

## 10. Auto-archiving

Meetups are archived automatically (status: published → past) 6 hours after
their event_date on every page load. To also run it via cron:

```bash
crontab -u apache -e
# Add:
0 * * * * /var/www/postgresql.istanbul/venv/bin/python \
  /var/www/postgresql.istanbul/django/manage.py shell -c \
  "from meetups.models import Meetup; Meetup.auto_archive()"
```

---

## Speaker photo uploads

Speaker photos are uploaded as files (JPG/PNG, max 5 MB) and stored under `MEDIA_ROOT`
(`django/media/speakers/` by default), served at `/media/speakers/...`.

After pulling this update, run migrations to add the new `speaker_photo` field:

```bash
source /var/www/postgresql.istanbul/venv/bin/activate
cd /var/www/postgresql.istanbul/django
python manage.py makemigrations meetups
python manage.py migrate
```

Create the media directory and ensure it's writable:

```bash
mkdir -p /var/www/postgresql.istanbul/django/media/speakers
chown -R apache:apache /var/www/postgresql.istanbul/django/media
```

The updated `deployment/apache.conf` adds an `/media` alias so Apache serves uploaded
photos directly (faster than proxying through Gunicorn). Re-copy it if you're updating
an existing deployment:

```bash
cp deployment/apache.conf /etc/httpd/conf.d/postgresql.istanbul.conf
apachectl configtest && systemctl reload httpd
```

When a speaker photo is replaced or removed via the admin panel, the old file is
automatically deleted from disk.

---

## Slide deck uploads

Speakers' slides (PDF only, max 25 MB) are uploaded via the admin panel and stored
under `MEDIA_ROOT/slides/`, served at `/media/slides/...`. A "Download Slides" link
appears on the public meetup page — for both the upcoming meetup and past meetups.

After pulling this update, run migrations to add the new `slides` field:

```bash
source /var/www/postgresql.istanbul/venv/bin/activate
cd /var/www/postgresql.istanbul/django
python manage.py makemigrations meetups
python manage.py migrate
```
