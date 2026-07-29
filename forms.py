from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class RegisterForm(FlaskForm):
    name = StringField(
        "Nome",
        validators=[DataRequired(message="Informe seu nome."), Length(max=120)],
    )
    email = StringField(
        "E-mail",
        validators=[
            DataRequired(message="Informe seu e-mail."),
            Email(message="E-mail inválido."),
            Length(max=255),
        ],
    )
    password = PasswordField(
        "Senha",
        validators=[
            DataRequired(message="Informe uma senha."),
            Length(min=8, max=128, message="A senha deve ter entre 8 e 128 caracteres."),
        ],
    )
    confirm_password = PasswordField(
        "Confirme a senha",
        validators=[
            DataRequired(message="Confirme sua senha."),
            EqualTo("password", message="As senhas não coincidem."),
        ],
    )
    submit = SubmitField("Cadastrar")


class LoginForm(FlaskForm):
    email = StringField(
        "E-mail",
        validators=[DataRequired(message="Informe seu e-mail."), Email(message="E-mail inválido.")],
    )
    password = PasswordField("Senha", validators=[DataRequired(message="Informe sua senha.")])
    submit = SubmitField("Entrar")


class DeleteAccountForm(FlaskForm):
    """Formulário vazio (só CSRF) usado para logout e exclusão de conta via POST."""

    submit = SubmitField("Deletar conta")
