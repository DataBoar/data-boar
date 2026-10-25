from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB


class MLClassifier:
    def __init__(self):
        # Carregar modelo treinado (exemplo com dados de treino)
        self.model = MultinomialNB()
        self.vectorizer = TfidfVectorizer()
        self.classes = ["Sensível", "Não Sensível"]

    def treinar(self, dados, labels):
        X = self.vectorizer.fit_transform(dados)
        self.model.fit(X, labels)

    def prever(self, texto):
        X = self.vectorizer.transform([texto])
        return self.model.predict(X)[0]
