<div align="center">

# 🇪🇹 EthioJobs — Enterprise Online Job Portal & ATS Platform

**A full-featured, production-ready recruitment ecosystem engineered for Ethiopian & African employment markets.**

[![Django](https://img.shields.io/badge/Django-5.1%2B-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![i18n](https://img.shields.io/badge/i18n-English%20%7C%20Amharic%20%7C%20Oromo%20%7C%20Tigrinya-success)](locale/)
[![Security](https://img.shields.io/badge/Security-Hardened%20(OWASP)-green)](jobs/settings.py)

[Live Demo](https://wubante.pythonanywhere.com/) • [Swagger API Docs](https://wubante.pythonanywhere.com/swagger/) • [Features](#-key-features) • [Installation](#-installation--setup) • [Deployment](#-deployment)

</div>

---

## 📖 Executive Summary

**EthioJobs Portal** is a modern, high-performance career platform and Applicant Tracking System (ATS) tailored specifically for emerging markets, regulatory standards, and multilingual workforces. It bridges candidates, companies, and platform administrators with features such as **AI-driven trade license forensics**, **Chapa payments**, **Telegram mini-app notifications**, **live employer-candidate messaging**, and **automated CV generation**.

---

## ✨ Key Features

### 1. 🛡️ Regulatory & Trade License Verification (Anti-Fraud)
- **Ministry of Trade (MoTRI) Compliance**: Required 10-digit TIN and commercial trade license upload for all employer vacancies.
- **AI-Powered OCR Forensics**: Integrates with Google Gemini 1.5 Flash Vision to inspect official ink stamps, business names, and TIN consistency on PDF and image licenses.
- **Admin Verification Queue & Audit Trail**: Real-time admin dashboard to review, approve, re-scan, or reject employer credentials with localized feedback.

### 2. 🔐 Authentication & Social Auth
- **Multi-Provider OAuth2**: One-click sign-in with **Google OAuth2** (including Google One-Tap) and **GitHub**.
- **Fail-Safe Session Architecture**: Custom exception middleware (`CustomSocialAuthExceptionMiddleware`) gracefully handling token expiry, network timeouts, or cancellation without 500 errors.
- **Role-Based Provisioning**: Dynamic role assignment (Job Seeker / Employee vs Employer / Recruiter) with distinct onboarding paths.

### 3. 💼 Candidate & Job Seeker Hub
- **ATS Resume/CV Auto-Builder**: Dynamic HTML5/CSS3 resume generator with real-time preview and one-click PDF export.
- **AI Profile Parser**: Automatically extracts experience, skills, and education from uploaded CVs.
- **Application Tracking & Quick Apply**: Real-time status tracker (Applied, Under Review, Interview Scheduled, Offer Made).
- **Favorites & Job Alerts**: Instant email alerts for newly posted vacancies matching saved criteria.

### 4. 🏢 Recruiter & Employer ATS
- **Vacancy Management**: Complete vacancy lifecycle (Draft, Pending Review, Active, Filled, Expired).
- **Candidate Evaluation**: Rating systems, candidate notes, interview scheduling, and CSV export for HR departments.
- **Company Branding Page**: Dedicated public employer directory with employee reviews and location maps.

### 5. 💬 Real-Time Communications
- **2-Way In-App Messaging**: Direct recruiter-to-candidate messaging with polling-based real-time sync.
- **Telegram Mini-App (TMA) & Channel Broadcast**: Automated job broadcasting to Telegram channels via Telegram Bot API.

### 6. 💳 Payments & Monetization
- **Chapa Payment Gateway Integration**: Native checkout for job posting fees, featured listings, and CV downloads via Telebirr, CBE Birr, and cards.
- **Automated Webhooks**: Instant transaction verification and invoice generation.

### 7. 🌍 Multilingual (i18n & l10n)
- Native support for four languages:
  - 🇬🇧 English (`en`)
  - 🇪🇹 Amharic (`am` / አማርኛ)
  - 🇪🇹 Afaan Oromoo (`om`)
  - 🇪🇹 Tigrinya (`ti` / ትግርኛ)
- Dynamic language switcher with persistent user session preferences.

---

## 🏗️ Architecture & Tech Stack

```
┌────────────────────────────────────────────────────────┐
│                   Web & Mobile Clients                 │
│  (Desktop Web, Mobile Web, Telegram WebApp Mini-App)   │
└───────────────────────────┬────────────────────────────┘
                            │ HTTPS / WSS
┌───────────────────────────▼────────────────────────────┐
│                    Nginx / Reverse Proxy               │
└───────────────────────────┬────────────────────────────┘
                            │ WSGI
┌───────────────────────────▼────────────────────────────┐
│                  Django Application Core               │
│                                                        │
│  ├── accounts/      (Auth, Roles, Company Verification)│
│  ├── jobsapp/       (Jobs, Search, ATS, Messaging)     │
│  ├── resume_cv/     (Templates, Auto CV Builder)       │
│  ├── payments/      (Chapa Gateway Integration)        │
│  └── jobs/          (Settings, Routing, Middlewares)   │
└────────┬──────────────────┬──────────────────┬─────────┘
         │                  │                  │
┌────────▼─────────┐ ┌──────▼──────┐ ┌─────────▼─────────┐
│ SQLite/PostgreSQL│ │ Gemini 1.5  │ │ Chapa / Telegram  │
│ Primary Database │ │ Vision OCR  │ │ External Webhooks │
└──────────────────┘ └─────────────┘ └───────────────────┘
```

---

## 🚀 Installation & Setup

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, or 3.14
- Git
- Virtualenv (`python -m venv venv`)

### 2. Clone the Repository
```bash
git clone https://github.com/wuba21/Django-online-Job-Portal-system.git
cd Django-online-Job-Portal-system
```

### 3. Set Up Virtual Environment
```bash
# On Linux / macOS:
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment Variables
```bash
cp .env.example .env
```
Open `.env` and fill in your values (or use defaults for local SQLite development).

### 6. Run Migrations & Compile Translations
```bash
python manage.py migrate
python scripts/compile_translations.py
```

### 7. Initialize Superuser / Admin
```bash
python scripts/setup_admin.py
```

### 8. Run Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 🧪 Testing & Verification

Run the comprehensive test suite and system sanity checks:
```bash
# Django system integrity check
python manage.py check

# Run automated tests
python manage.py test
```

---

## 📦 Deployment

### Production Deployment on PythonAnywhere

1. Open your PythonAnywhere Bash Console.
2. Run the deployment script or single-line updater:
```bash
cd /home/wubante/Django-online-Job-Portal-system && git pull origin master && python manage.py migrate && python scripts/compile_translations.py && python manage.py collectstatic --noinput && touch /var/www/wubante_pythonanywhere_com_wsgi.py
```

### Docker Deployment
```bash
# Development
docker-compose up -d --build

# Production
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 🔒 Security Best Practices
- **Strict Cookie Flags**: `SESSION_COOKIE_SAMESITE = "Lax"`, `CSRF_COOKIE_SAMESITE = "Lax"`, and `HTTPONLY` enabled.
- **OWASP Hardening**: `X_FRAME_OPTIONS = "DENY"`, `SECURE_CONTENT_TYPE_NOSNIFF`, and HSTS preloading in production.
- **Zero Secrets in Repo**: All keys (`SECRET_KEY`, `CHAPA_SECRET_KEY`, `GEMINI_API_KEY`) loaded strictly from environment.
- **Structured 12-Factor Logging**: Consolidated console error streams with timestamps for instant debugging without swallowing exceptions.

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
