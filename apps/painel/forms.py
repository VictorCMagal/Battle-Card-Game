"""Formulários do painel administrativo."""
import csv
import io

from django import forms

from apps.accounts import rules
from apps.accounts.models import AccCode, Conta
from apps.cards import schema
from apps.core.models import ConfigServidor, Servidor


class ContaAdminForm(forms.ModelForm):
    """Edição de conta. A senha só muda se `nova_senha` for preenchida (e válida)."""
    nova_senha = forms.CharField(required=False, widget=forms.PasswordInput(render_value=False),
                                 help_text="Deixe em branco para manter.")

    class Meta:
        model = Conta
        fields = ["acc_code", "premium_check", "cur_battlepoints", "cur_magicdust", "cur_cash",
                  "acc_score", "victory_counts", "selected_deck"]

    def __init__(self, *args, editor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.editor = editor
        if editor is not None and editor.acc_code != AccCode.DEV:
            # ADMIN não concede nem retira perfis privilegiados
            self.fields["acc_code"].choices = [c for c in AccCode.choices if c[0] not in ("DEV", "ADMIN")]

    def clean_acc_code(self):
        code = self.cleaned_data["acc_code"]
        if self.editor and self.editor.acc_code != AccCode.DEV and self.instance.acc_code in ("DEV", "ADMIN"):
            raise forms.ValidationError("Somente DEV altera contas privilegiadas.")
        return code

    def clean_nova_senha(self):
        pw = self.cleaned_data.get("nova_senha")
        if pw and rules.validate_password(pw):
            raise forms.ValidationError("A senha deve ter de 6 a 32 caracteres.")
        return pw

    def save(self, commit=True):
        conta = super().save(commit=False)
        if self.cleaned_data.get("nova_senha"):
            conta.set_password(self.cleaned_data["nova_senha"])
        if commit:
            conta.save()
        return conta


class CartaForm(forms.Form):
    """Cadastro/edição de carta. Campos compostos usam o mesmo formato do CSV de importação."""
    card_id = forms.IntegerField(min_value=1, label="Card_ID")
    type = forms.ChoiceField(choices=[(t, t) for t in schema.CARD_TYPES])
    name = forms.CharField(max_length=64)
    rarity = forms.CharField(max_length=16, initial="common")
    power = forms.IntegerField(initial=1)
    power_bonus = forms.IntegerField(initial=0)
    attack_bonus = forms.IntegerField(initial=0)
    damage = forms.IntegerField(initial=0)
    shield = forms.IntegerField(initial=0)
    mana_cost = forms.IntegerField(initial=0)
    elements = forms.CharField(required=False, help_text="Ex.: F|I (até 4; E S F W I A M U B)")
    mana_gains = forms.CharField(required=False, help_text="Ex.: F:2|I:-1 (até 4; valores -3..3)")
    skills = forms.CharField(required=False, help_text="slot:nome:número:custo:txt_key | ... (até 3)")

    def to_card_dict(self) -> dict:
        d = self.cleaned_data
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(schema.CSV_COLUMNS)
        w.writerow([d[k] for k in schema.CSV_COLUMNS])
        rows = schema.parse_csv(buf.getvalue())
        return rows[0]

    def clean(self):
        data = super().clean()
        if self.errors:
            return data
        try:
            card = self.to_card_dict()
        except (ValueError, IndexError):
            raise forms.ValidationError("Formato inválido em elements/mana_gains/skills.")
        errs = schema.validate_card_dict(card)
        if errs:
            raise forms.ValidationError(errs)
        return data


class ImportForm(forms.Form):
    arquivo = forms.FileField(help_text="JSON (lista ou {\"cards\": [...]}) ou CSV")
    sobrescrever = forms.BooleanField(required=False, initial=True,
                                      help_text="Atualiza cartas com Card_ID já existente")


class ServidorForm(forms.ModelForm):
    class Meta:
        model = Servidor
        fields = ["name", "active"]


class ConfigForm(forms.ModelForm):
    class Meta:
        model = ConfigServidor
        fields = ["key", "value"]
