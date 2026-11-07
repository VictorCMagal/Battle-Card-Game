"""Regras de validação de cadastro (O§1) em Python puro, compartilhadas por forms/API/testes.

Cada função retorna uma lista de chaves de erro (traduzidas em locale/pt_BR). Lista vazia = válido.
"""
import re

NAME_MIN, NAME_MAX = 4, 16        # "maior que 3 e no máximo 16" (D-02)
PASSWORD_MIN, PASSWORD_MAX = 6, 32  # regra da senha DIGITADA (o hash usa coluna maior)
EMAIL_MIN, EMAIL_MAX = 4, 64      # "mais de 3 caracteres"; coluna VARCHAR(64) (D-01)

_NAME_RE = re.compile(r"^[A-Za-z0-9]+$")   # sem acentos/especiais/espaços (D-02)


def validate_name(name: str) -> list:
    errors = []
    name = name or ""
    if len(name) < NAME_MIN or len(name) > NAME_MAX:
        errors.append("err.name_length")
    if name and not _NAME_RE.match(name):
        errors.append("err.name_chars")
    return errors


def validate_password(password: str, confirm=None) -> list:
    errors = []
    password = password or ""
    if len(password) < PASSWORD_MIN or len(password) > PASSWORD_MAX:
        errors.append("err.password_length")
    if confirm is not None and password != confirm:
        errors.append("err.password_mismatch")
    return errors


def validate_email(email: str) -> list:
    """Regra do original: >3 caracteres, com '@' e ao menos um '.' após o '@'."""
    errors = []
    email = (email or "").strip()
    if len(email) < EMAIL_MIN or len(email) > EMAIL_MAX:
        errors.append("err.email_length")
        return errors
    at = email.find("@")
    domain = email[at + 1:] if at > 0 else ""
    if (at <= 0 or email.count("@") != 1 or " " in email or "." not in domain
            or domain.startswith(".") or domain.endswith(".")):
        errors.append("err.email_format")
    return errors


def validate_registration(name, password, confirm, email) -> dict:
    """Valida todos os campos. Retorna {campo: [chaves de erro]} apenas com campos inválidos."""
    result = {
        "name": validate_name(name), "password": validate_password(password, confirm),
        "email": validate_email(email),
    }
    return {k: v for k, v in result.items() if v}
