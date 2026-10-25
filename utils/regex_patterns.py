import re


class RegexPatterns:
    CPF = r"^\d{3}\.\d{3}\.\d{3}-\d{2}$"  # CPF brasileiro
    RG = r"^\d{2}\.\d{3}\.\d{3}-\d{1}$"  # RG brasileiro
    EMAIL = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"  # E-mail
    GENERO = r"^(Masculino|Feminino|Outro|Indefinido)$"  # Gênero
    DADOS_SAUDE = r"^(CNPJ|CRM|NIS|PIS|PASEP|CNS|CPF|RG)$"  # Dados de saúde
    AFILIAÇÃO_POLÍTICA = r"^(CNPJ|CPF|RG|NIS|NIS-PP)$"  # Afiliação política
    DATA_NASCIMENTO = r"^\d{2}\/\d{2}\/\d{4}$"  # Data de nascimento

    @classmethod
    def validar_dado(cls, dado, tipo):
        if tipo == "CPF":
            return re.match(cls.CPF, dado)
        elif tipo == "RG":
            return re.match(cls.RG, dado)
        elif tipo == "EMAIL":
            return re.match(cls.EMAIL, dado)
        elif tipo == "GENERO":
            return re.match(cls.GENERO, dado)
        elif tipo == "DADOS_SAUDE":
            return re.match(cls.DADOS_SAUDE, dado)
        elif tipo == "AFILIAÇÃO_POLÍTICA":
            return re.match(cls.AFILIAÇÃO_POLÍTICA, dado)
        elif tipo == "DATA_NASCIMENTO":
            return re.match(cls.DATA_NASCIMENTO, dado)
        return None
