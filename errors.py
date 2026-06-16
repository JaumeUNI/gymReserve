"""
Error d'API.

Una excepció senzilla per als errors de negoci. Quan un servei detecta que
alguna cosa no és vàlida (no hi ha places, email duplicat, etc.), llança un
APIError amb el codi HTTP i el missatge. main.py captura aquests errors i els
converteix en una resposta JSON amb el codi corresponent.
"""


class APIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)
