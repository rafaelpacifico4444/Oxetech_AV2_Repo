import os


class Config:
    """Configuração da aplicação lida a partir de variáveis de ambiente.

    Em produção, essas variáveis são injetadas pelo systemd via
    /etc/app.env (gerado pelo user-data.sh a partir do Terraform).
    Nunca deixe segredos hardcoded aqui.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY não definida. Defina a variável de ambiente SECRET_KEY "
            "(deve ser igual em todas as instâncias, pois assina o cookie de sessão)."
        )

    DB_HOST = os.environ.get("DB_HOST")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_NAME = os.environ.get("DB_NAME")
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")

    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        raise RuntimeError(
            "Variáveis de conexão com o banco incompletas "
            "(DB_HOST, DB_NAME, DB_USER, DB_PASSWORD)."
        )

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,  # evita erros com conexões RDS derrubadas por inatividade
    }

    # Cookies de sessão: a app fica atrás do ALB, que termina TLS e encaminha
    # X-Forwarded-Proto. SESSION_COOKIE_SECURE=True exige HTTPS para o cookie
    # ser enviado — combine com ProxyFix (ver app.py) para funcionar corretamente.
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "true").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_HTTPONLY = True

    WTF_CSRF_ENABLED = True
