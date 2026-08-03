import os
import urllib.request
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from extensions import db, login_manager, bcrypt, csrf
from models import User
from forms import LoginForm, RegisterForm, DeleteAccountForm


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Suporte para Reverse Proxy / Load Balancer (ALB) da AWS
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # Inicializa as extensões
    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        # Uso do db.session.get (padrão do SQLAlchemy moderno)
        return db.session.get(User, int(user_id))

    # Auxiliar para metadados diretos da AWS (IMDSv2)
    def obter_metadata_aws(endpoint: str) -> str:
        try:
            req_token = urllib.request.Request(
                "http://169.254.169.254/latest/api/token",
                headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"},
                method="PUT"
            )
            token = urllib.request.urlopen(req_token, timeout=1).read().decode()

            req_data = urllib.request.Request(
                f"http://169.254.169.254/latest/meta-data/{endpoint}",
                headers={"X-aws-ec2-metadata-token": token}
            )
            return urllib.request.urlopen(req_data, timeout=1).read().decode().strip()
        except Exception:
            return None

    # Auxiliar para ler arquivo local ou consultar metadados AWS
    def ler_arquivo(caminho: str, ec2_metadata_path: str = None) -> str:
        try:
            if os.path.exists(caminho):
                with open(caminho, "r", encoding="utf-8") as f:
                    conteudo = f.read().strip()
                    if conteudo:
                        return conteudo
        except Exception:
            pass

        if ec2_metadata_path:
            meta = obter_metadata_aws(ec2_metadata_path)
            if meta:
                return meta

        return "indisponível"

    with app.app_context():
        db.create_all()

    # ── ROTAS ──

    @app.route("/health")
    def health():
        return "ok", 200

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        form = RegisterForm()
        if form.validate_on_submit():
            # Tratamento de e-mail limpo e em minúsculas
            email = form.email.data.strip().lower()

            if User.query.filter_by(email=email).first():
                flash("Este e-mail já está cadastrado.", "danger")
                return render_template("register.html", form=form)

            password_hash = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
            user = User(
                name=form.name.data.strip(),
                email=email,
                password_hash=password_hash
            )
            db.session.add(user)
            db.session.commit()

            flash("Cadastro realizado com sucesso! Faça login.", "success")
            return redirect(url_for("login"))

        return render_template("register.html", form=form)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        form = LoginForm()
        if form.validate_on_submit():
            # Tratamento de e-mail limpo e em minúsculas
            email = form.email.data.strip().lower()
            user = User.query.filter_by(email=email).first()

            if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Login realizado com sucesso!", "success")
                return redirect(url_for("dashboard"))

            flash("E-mail ou senha inválidos.", "danger")

        return render_template("login.html", form=form)

    @app.route("/dashboard")
    @login_required
    def dashboard():
        instance_id = ler_arquivo("/var/lib/app/instance-id", "instance-id")
        az = ler_arquivo("/var/lib/app/az", "placement/availability-zone")
        ip_local = ler_arquivo("/var/lib/app/ip", "local-ipv4")
        servido_em = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        delete_form = DeleteAccountForm()

        return render_template(
            "dashboard.html",
            user=current_user,
            instance_id=instance_id,
            az=az,
            ip_local=ip_local,
            servido_em=servido_em,
            delete_form=delete_form,
        )

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        flash("Você saiu da sua conta.", "info")
        return redirect(url_for("login"))

    @app.route("/delete-account", methods=["POST"])
    @login_required
    def delete_account():
        form = DeleteAccountForm()
        if form.validate_on_submit():
            user = db.session.get(User, current_user.id)
            logout_user()
            db.session.delete(user)
            db.session.commit()
            flash("Sua conta foi deletada.", "info")
            return redirect(url_for("login"))

        return redirect(url_for("dashboard"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)