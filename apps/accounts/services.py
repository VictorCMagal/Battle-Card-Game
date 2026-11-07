"""Casos de uso de conta: cadastro (com deck inicial) e payload público do usuário."""
from django.db import IntegrityError, transaction

from apps.core.errors import ServiceError

from .models import Conta


def user_payload(u: Conta) -> dict:
    """Dados da conta enviados ao cliente (nunca hash, PIN ou e-mail de terceiros)."""
    return {"id": u.id, "name": u.name, "email": u.email, "acc_code": u.acc_code,
            "battlepoints": u.cur_battlepoints, "magicdust": u.cur_magicdust, "cash": u.cur_cash,
            "score": u.acc_score, "victories": u.victory_counts, "selected_deck": u.selected_deck,
            "premium": u.premium_check, "is_admin": u.is_staff}


def name_taken(name: str) -> bool:
    return Conta.objects.filter(name__iexact=name).exists()


def email_taken(email: str) -> bool:
    return Conta.objects.filter(email__iexact=email.strip()).exists()


def register_account(name, email, password, rng=None, acc_code="GREEN") -> Conta:
    """Cria a conta, o Grimorium (vazio) e o deck inicial com 40 cartas aleatórias (D-03).

    A unicidade é verificada dentro da transação; colisões concorrentes viram ServiceError."""
    from apps.decks.services import create_starter_setup
    try:
        with transaction.atomic():
            if name_taken(name):
                raise ServiceError("err.name_taken", 409)
            if email_taken(email):
                raise ServiceError("err.email_taken", 409)
            conta = Conta.objects.create_conta(name, email, password, acc_code=acc_code)
            create_starter_setup(conta, rng=rng)
            return conta
    except IntegrityError:
        raise ServiceError("err.name_or_email_taken", 409)
