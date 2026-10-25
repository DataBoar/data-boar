from utils.regex_patterns import RegexPatterns
from utils.ml_classifier import MLClassifier


class DataScanner:
    def __init__(self, db_connector):
        self.db_connector = db_connector
        self.regex_patterns = RegexPatterns()
        self.ml_classifier = MLClassifier()

    def validar_dado(self, dado, tipo):
        regex_result = self.regex_patterns.validar_dado(dado, tipo)
        ml_result = (
            self.ml_classifier.prever(dado)
            if tipo in ["CPF", "RG", "EMAIL", "DATA_NASCIMENTO"]
            else None
        )
        return {
            "tipo": tipo,
            "valor": dado,
            "regex_match": bool(regex_result),
            "ml_classification": ml_result,
        }

    def scan(self):
        resultados = []
        for db_name, conn in self.db_connector.connections.items():
            # Simular consulta a tabela (exemplo)
            for linha in self.simular_consulta(db_name):
                for coluna, valor in linha.items():
                    tipo = self.determinar_tipo_dado(coluna)
                    resultado = self.validar_dado(valor, tipo)
                    resultados.append(resultado)
        return resultados

    def simular_consulta(self, db_name):
        # Simulação de consulta SQL (exemplo)
        return [
            {
                "CPF": "123.456.789-00",
                "Email": "usuario@example.com",
                "RG": "12.345.678-9",
                "DataNascimento": "01/01/2000",
            }
        ]

    def determinar_tipo_dado(self, coluna):
        # Lógica para identificar tipo de dado (ex: "CPF", "Email", etc.)
        if "cpf" in coluna.lower():
            return "CPF"
        elif "rg" in coluna.lower():
            return "RG"
        elif "email" in coluna.lower():
            return "EMAIL"
        elif "data" in coluna.lower():
            return "DATA_NASCIMENTO"
        return "GERAL"
