from flask import Flask, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from extensions import db, login_manager, bcrypt, csrf
from models import User
from forms import RegisterForm, LoginForm, DeleteAccountForm


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # A app roda atrás do ALB (TLS termina lá). ProxyFix garante que
    # request.is_secure e url_for(..., _external=True) respeitem o
    # cabeçalho X-Forwarded-Proto enviado pelo load balancer.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Faça login para acessar essa página."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    with app.app_context():
        db.create_all()

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
            email = form.email.data.strip().lower()
            if User.query.filter_by(email=email).first():
                flash("Este e-mail já está cadastrado.", "danger")
                return render_template("register.html", form=form)

            password_hash = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
            user = User(name=form.name.data.strip(), email=email, password_hash=password_hash)
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
            email = form.email.data.strip().lower()
            user = User.query.filter_by(email=email).first()

            if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Login realizado com sucesso!", "success")
                return redirect(url_for("dashboard"))

            # Mensagem genérica de propósito: não revela se o e-mail existe ou não.
            flash("E-mail ou senha inválidos.", "danger")

        return render_template("login.html", form=form)

    @app.route("/dashboard")
    @login_required
    def dashboard():
        delete_form = DeleteAccountForm()
        return render_template("dashboard.html", user=current_user, delete_form=delete_form)

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

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)


