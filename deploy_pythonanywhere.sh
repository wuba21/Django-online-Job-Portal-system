#!/bin/bash
# ============================================================
#  ETHIO JOBS PORTAL — PythonAnywhere Deployment Script
#  Run this inside PythonAnywhere Bash Console
#  Username: wubante   |  Site: wubante.pythonanywhere.com
# ============================================================

set -e   # Stop on any error

# ─── SETTINGS — YOUR USERNAME ──────────────────────────────
PA_USER="wubante"
PROJECT_NAME="django-job-portal"
REPO_URL="https://github.com/wuba21/${PROJECT_NAME}.git"     # ← GitHub URL yih new (change if different)
PA_HOME="/home/${PA_USER}"
PROJECT_DIR="${PA_HOME}/${PROJECT_NAME}"
VENV_DIR="${PA_HOME}/venv_jobportal"
PYTHON="${VENV_DIR}/bin/python"
PIP="${VENV_DIR}/bin/pip"
MANAGE="${PROJECT_DIR}/manage.py"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║       ETHIO JOBS PORTAL — PYTHONANYWHERE DEPLOY      ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ─── STEP 1: Clone or Pull latest code ─────────────────────
echo "📦 STEP 1: Getting latest code..."
if [ -d "${PROJECT_DIR}/.git" ]; then
    echo "→ Repo exists. Pulling latest changes..."
    cd "${PROJECT_DIR}"
    git pull origin main
else
    echo "→ Cloning repo for the first time..."
    cd "${PA_HOME}"
    git clone "${REPO_URL}" "${PROJECT_NAME}"
    cd "${PROJECT_DIR}"
fi

# ─── STEP 2: Create / activate virtualenv ──────────────────
echo ""
echo "🐍 STEP 2: Setting up Python virtual environment..."
if [ ! -d "${VENV_DIR}" ]; then
    echo "→ Creating new virtualenv..."
    python3.10 -m venv "${VENV_DIR}"
fi
echo "→ Virtualenv ready at ${VENV_DIR}"

# ─── STEP 3: Install / update requirements ─────────────────
echo ""
echo "📋 STEP 3: Installing requirements..."
${PIP} install --upgrade pip --quiet
${PIP} install -r "${PROJECT_DIR}/requirements.txt" --quiet
echo "→ All packages installed."

# ─── STEP 4: Setup .env file ───────────────────────────────
echo ""
echo "🔑 STEP 4: Checking .env file..."
ENV_FILE="${PROJECT_DIR}/.env"

if [ ! -f "${ENV_FILE}" ]; then
    echo "→ .env not found — creating from sample..."
    cat > "${ENV_FILE}" << 'ENVEOF'
DEBUG=False
SECRET_KEY=change-this-to-a-very-long-random-secret-key-at-least-50-chars

# Database (SQLite default — change for MySQL)
# DATABASE_URL=mysql://user:pass@host/dbname

# Payment
CHAPA_SECRET_KEY=CHASECK_TEST-LpIMynCSj89EOX7AgFurw1o6d7M9sLca

# Telegram
TELEGRAM_BOT_TOKEN=8487911861:AAEtEz13n_5PcZKiXCP9e8ouHlS0kiSW-b4
TELEGRAM_CHAT_ID=@ethio_jobportal

# Social Auth
SOCIAL_AUTH_GITHUB_KEY=your_github_key_here
SOCIAL_AUTH_GITHUB_SECRET=your_github_secret_here
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your_google_client_id_here
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your_google_secret_here
SOCIAL_AUTH_FACEBOOK_KEY=your_facebook_app_id
SOCIAL_AUTH_FACEBOOK_SECRET=your_facebook_app_secret
SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY=your_linkedin_client_id
SOCIAL_AUTH_LINKEDIN_OAUTH2_SECRET=your_linkedin_client_secret
ENVEOF
    echo "⚠  .env created. IMPORTANT: Change SECRET_KEY before going live!"
else
    echo "→ .env already exists. Updating DEBUG=False..."
    sed -i 's/^DEBUG=True/DEBUG=False/' "${ENV_FILE}"
fi

# ─── STEP 5: Run migrations ────────────────────────────────
echo ""
echo "🗃  STEP 5: Running database migrations..."
cd "${PROJECT_DIR}"
${PYTHON} ${MANAGE} migrate --noinput
echo "→ Migrations applied."

# ─── STEP 6: Collect static files ──────────────────────────
echo ""
echo "🎨 STEP 6: Collecting static files..."
${PYTHON} ${MANAGE} collectstatic --noinput --clear
echo "→ Static files collected."

# ─── STEP 7: Compile translation messages ──────────────────
echo ""
echo "🌐 STEP 7: Compiling translation messages..."
${PYTHON} ${MANAGE} compilemessages 2>/dev/null && echo "→ Messages compiled." || echo "→ No messages to compile (OK)."

# ─── STEP 8: Create superuser (first time only) ────────────
echo ""
echo "👤 STEP 8: Superuser setup..."
${PYTHON} -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobs.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        email='admin@ethiojobs.com',
        password='Admin@1234',
        first_name='Admin',
        last_name='User',
        role='employer'
    )
    print('→ Superuser created: admin@ethiojobs.com / Admin@1234')
    print('  ⚠  Change password after first login!')
else:
    print('→ Superuser already exists. Skipped.')
"

# ─── STEP 9: Django system check ───────────────────────────
echo ""
echo "🔍 STEP 9: Django system check..."
${PYTHON} ${MANAGE} check --deploy 2>&1 | tail -5
echo ""

# ─── DONE ──────────────────────────────────────────────────
echo "╔══════════════════════════════════════════════════════╗"
echo "║                   ✅  DEPLOY DONE!                   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "  🌍 Site URL : https://wubante.pythonanywhere.com"
echo "  🔧 Admin    : https://wubante.pythonanywhere.com/admin/"
echo ""
echo "  📌 NEXT — Go to PythonAnywhere Web tab and:"
echo "     1. Source code  : ${PROJECT_DIR}"
echo "     2. Working dir  : ${PROJECT_DIR}"
echo "     3. Virtualenv   : ${VENV_DIR}"
echo "     4. WSGI file    → edit to point to jobs.wsgi"
echo "     5. Static files : URL=/static/  Path=${PROJECT_DIR}/staticfiles"
echo "     6. Media files  : URL=/media/   Path=${PROJECT_DIR}/media"
echo "     7. Click 🔄 Reload"
echo ""
