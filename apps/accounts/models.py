"""Tabela Conta (O§2.1) como modelo de usuário customizado do Django.

Nomes de colunas seguem o original (`acc_password`, `login_datatime`, `Selected_Deck`...).
Desvios autorizados (D-01): `acc_password` guarda o HASH do Django (VARCHAR(128)), `email`
VARCHAR(64), `acc_pin` anulável (sem fluxo de PIN no MVP) e `codigo_id` gerado no cadastro.
"""
import secrets

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class AccCode(models.TextChoices):
    """Perfil da conta: DEV/ADMIN acessam o painel; RED é bloqueada; GRAY é reservado (D-04)."""
    DEV = "DEV", "Desenvolvedor"
    ADMIN = "ADMIN", "Administrador"
    GRAY = "GRAY", "Reservado"
    GREEN = "GREEN", "Jogador"
    RED = "RED", "Bloqueado"


class ContaManager(BaseUserManager):
    def get_by_natural_key(self, name):
        """Login sem diferenciar maiúsculas/minúsculas."""
        return self.get(name__iexact=name)

    def _new_codigo(self) -> int:
        while True:
            code = secrets.randbelow(900_000_000) + 100_000_000
            if not self.filter(codigo_id=code).exists():
                return code

    def create_conta(self, name, email, password, acc_code=AccCode.GREEN, **extra):
        conta = self.model(name=name, email=(email or "").strip(), acc_code=acc_code,
                           codigo_id=self._new_codigo(), **extra)
        conta.set_password(password)
        conta.save(using=self._db)
        return conta

    create_user = create_conta

    def create_superuser(self, name, email, password=None, **extra):
        return self.create_conta(name, email, password, acc_code=AccCode.DEV, **extra)


class Conta(AbstractBaseUser):
    codigo_id = models.IntegerField(unique=True, editable=False)
    acc_status = models.SmallIntegerField(default=0)  # 0 criada, 1 starter deck, 2 e-mail ok, 3 PIN ok
    name = models.CharField(max_length=16, unique=True)
    email = models.CharField(max_length=64, unique=True)
    birth_datatime = models.DateTimeField(null=True, blank=True)
    # campos herdados com nomes de coluna do original
    password = models.CharField(max_length=128, db_column="acc_password")
    last_login = models.DateTimeField(null=True, blank=True, db_column="login_datatime")
    acc_pin = models.CharField(max_length=128, null=True, blank=True)
    acc_score = models.IntegerField(default=0)
    acc_code = models.CharField(max_length=5, choices=AccCode.choices, default=AccCode.GREEN)
    victory_counts = models.IntegerField(default=0)
    premium_check = models.BooleanField(default=False)
    premium_score = models.IntegerField(null=True, blank=True)
    premium_datetime = models.DateTimeField(null=True, blank=True)
    selected_deck = models.PositiveSmallIntegerField(default=1, db_column="Selected_Deck")
    deck_1 = models.ForeignKey("decks.Deck", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    deck_2 = models.ForeignKey("decks.Deck", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    deck_3 = models.ForeignKey("decks.Deck", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    deck_4 = models.ForeignKey("decks.Deck", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    deck_5 = models.ForeignKey("decks.Deck", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    deck_6 = models.ForeignKey("decks.Deck", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    grimorium = models.ForeignKey("decks.Grimorium", null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name="+")
    cur_battlepoints = models.IntegerField(default=0)
    cur_magicdust = models.IntegerField(default=0)
    cur_cash = models.IntegerField(default=0)  # U$1.00 = 100 (centavos); sem loja no MVP
    last_session_key = models.CharField(max_length=40, null=True, blank=True)  # sessão única (D-26)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "name"
    REQUIRED_FIELDS = ["email"]
    objects = ContaManager()

    class Meta:
        db_table = "Conta"

    def __str__(self):
        return self.name

    # --- permissões derivadas do acc_code (compatíveis com o Django Admin) ---
    @property
    def is_active(self):
        return self.acc_code != AccCode.RED

    @property
    def is_staff(self):
        return self.acc_code in (AccCode.DEV, AccCode.ADMIN)

    @property
    def is_superuser(self):
        return self.acc_code == AccCode.DEV

    @property
    def is_admin_user(self):
        return self.is_staff

    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_staff

    def deck_for_slot(self, slot: int):
        return getattr(self, f"deck_{slot}", None) if 1 <= slot <= 6 else None
