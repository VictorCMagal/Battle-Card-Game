"""Erros de regra do motor. O `code` é uma chave de tradução (locale/pt_BR)."""


class GameError(Exception):
    """Ação inválida segundo as regras. Nunca altera o estado quando levantada."""

    def __init__(self, code: str, **params):
        super().__init__(code)
        self.code = code
        self.params = params
