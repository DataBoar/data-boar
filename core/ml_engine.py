import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier


class MLSensitivityScanner:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        self.model = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            min_samples_leaf=1,
            max_features="sqrt",
            n_jobs=1,
        )
        self.is_trained = False
        self._load_or_train_initial_model()

    def _load_or_train_initial_model(self):
        """Treina um modelo base com exemplos de LGPD/GDPR/CCPA."""
        # Dados de treino sintéticos (em um cenário real, carregar de um dataset)
        data = {
            "text": [
                "cpf",
                "cadastro pessoa fisica",
                "social security number",
                "credit card",
                "email address",
                "nome completo",
                "data de nascimento",
                "birth date",
                "medical record",
                "prontuario medico",
                "religion",
                "political opinion",
                "id_interno",
                "quantidade_estoque",
                "cor_carro",
                "log_sistema",
            ],
            "label": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
        }
        df = pd.DataFrame(data)
        x = self.vectorizer.fit_transform(df["text"])
        self.model.fit(x, df["label"])
        self.is_trained = True

    def predict_sensitivity(self, text):
        """Retorna a probabilidade de um campo ser sensível (0.0 a 1.0)."""
        if not text:
            return 0.0
        x_input = self.vectorizer.transform([str(text).lower()])
        # Retorna a probabilidade da classe 1 (Sensível)
        prob = self.model.predict_proba(x_input)[0][1]
        return prob
