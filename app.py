import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from config import Config
from extensions import db, login_manager, bcrypt, csrf
from models import User
from forms import LoginForm, RegisterForm, DeleteAccountForm


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

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
        return User.query.get(int(user_id))

    # Função auxiliar para ler os arquivos de infraestrutura da AWS
    def ler_arquivo(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return "indisponível"

    # ── ROTAS ──

    @app.route("/dashboard")
    @login_required
    def dashboard():
        # Lê as métricas da instância
        instance_id = ler_arquivo("/var/lib/app/instance-id")
        az = ler_arquivo("/var/lib/app/az")
        ip_local = ler_arquivo("/var/lib/app/ip")
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

    # (Adicione suas outras rotas como /login, /register, etc. aqui)

    return app


app = create_app()

if __name__ == "__main__":
    app.run()