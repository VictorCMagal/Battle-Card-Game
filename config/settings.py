"""Configuração do projeto. Todos os segredos e ambientes vêm do arquivo .env (P§9)."""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
if (BASE_DIR / ".env").exists():
    environ.Env.read_env(str(BASE_DIR / ".env"))

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

INSTALLED_APPS = [
    "daphne",  # deve ser o primeiro: runserver passa a servir ASGI/WebSocket
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "channels",
    "apps.core", "apps.accounts", "apps.cards", "apps.decks", "apps.game", "apps.chat", "apps.painel",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "config.urls"
ASGI_APPLICATION = "config.asgi.application"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "frontend" / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

# --- Banco de dados -------------------------------------------------------------------------
# MySQL é o banco oficial. `DB_ENGINE=sqlite` existe apenas para rodar a suíte de testes Django
# rapidamente sem MySQL (não use em produção).
if env("DB_ENGINE", default="mysql") == "sqlite":
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
else:
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DB_NAME", default="battle_card_game"),
        "USER": env("DB_USER", default="root"),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "HOST": env("DB_HOST", default="127.0.0.1"),
        "PORT": env("DB_PORT", default="3306"),
        "CONN_MAX_AGE": 0,
        "OPTIONS": {"charset": "utf8mb4", "init_command": "SET sql_mode='STRICT_TRANS_TABLES'"},
    }}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Autenticação ----------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.Conta"
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]
LOGIN_URL = "/login/"

# --- Sessão / cookies / segurança ---------------------------------------------------------
_secure = env.bool("SECURE_COOKIES", default=False)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = _secure
CSRF_COOKIE_HTTPONLY = True   # o token é lido de <meta name="csrf-token">
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = _secure
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_AGE = 60 * 60 * 12

# --- Internacionalização ------------------------------------------------------------------
IDIOMA = env("IDIOMA", default="PT-BR")
LANGUAGE_CODE = "pt-br"
TIME_ZONE = env("TIME_ZONE", default="America/Sao_Paulo")
USE_I18N = True
USE_TZ = True

# --- Estáticos ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "frontend" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
WHITENOISE_USE_FINDERS = DEBUG
WHITENOISE_AUTOREFRESH = DEBUG

# --- Channels ------------------------------------------------------------------------------
if env("CHANNEL_LAYER", default="memory") == "redis":
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels_redis.core.RedisChannelLayer",
                                  "CONFIG": {"hosts": [env("REDIS_URL", default="redis://127.0.0.1:6379/0")]}}}
else:  # um único processo (Daphne). O estado das partidas já é por processo (P§19).
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

# --- Regras de aplicação ----------------------------------------------------------------
CHAT_MAX_LEN = 126
CHAT_RATE = (5, 5.0)           # 5 mensagens a cada 5 segundos
RECONNECT_SECONDS = 120        # janela de reconexão em partida (D-23)
ROOM_IDLE_SECONDS = 30         # sala sem conexão do jogador é removida
LOGIN_RATE = (10, 300.0)       # 10 tentativas / 5 min por IP+nome
CHAT_RETENTION_DAYS = 30

from config.logging_conf import build_logging  # noqa: E402
LOG_DIR = BASE_DIR / env("LOG_DIR", default="logs")
LOGGING = build_logging(LOG_DIR, env("LOG_LEVEL", default="INFO"))
