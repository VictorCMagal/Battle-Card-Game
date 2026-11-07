"""Cria uma conta ADMIN (ou DEV) pedindo a senha no terminal. Uso: manage.py createadmin NOME EMAIL [--dev]"""
import getpass

from django.core.management.base import BaseCommand, CommandError

from apps.accounts import rules, services
from apps.accounts.models import AccCode


class Command(BaseCommand):
    help = "Cria uma conta administrativa (ADMIN ou DEV)."

    def add_arguments(self, parser):
        parser.add_argument("name")
        parser.add_argument("email")
        parser.add_argument("--dev", action="store_true", help="cria como DEV em vez de ADMIN")

    def handle(self, *args, **opts):
        errs = rules.validate_name(opts["name"]) + rules.validate_email(opts["email"])
        if errs:
            raise CommandError(f"Dados inválidos: {errs}")
        password = getpass.getpass("Senha: ")
        if password != getpass.getpass("Repita a senha: "):
            raise CommandError("As senhas não conferem.")
        errs = rules.validate_password(password)
        if errs:
            raise CommandError(f"Senha inválida: {errs}")
        if services.name_taken(opts["name"]) or services.email_taken(opts["email"]):
            raise CommandError("Nome ou e-mail já cadastrado.")
        code = AccCode.DEV if opts["dev"] else AccCode.ADMIN
        services.register_account(opts["name"], opts["email"], password, acc_code=code)
        self.stdout.write(self.style.SUCCESS(f"Conta {code} '{opts['name']}' criada."))
