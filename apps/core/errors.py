"""Erro de serviço com chave de tradução, convertido em resposta JSON pelas views."""


class ServiceError(Exception):
    def __init__(self, code: str, status: int = 400, **params):
        super().__init__(code)
        self.code, self.status, self.params = code, status, params
