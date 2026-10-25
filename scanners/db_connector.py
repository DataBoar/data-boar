from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from utils.logger import Logger


class DBConnector:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.connections = {}

    def connect(self, db_url: str):
        try:
            self.engine = create_engine(db_url)
            self.connections["main"] = self.engine
            self.logger.info("Conexão estabelecida com o banco de dados")
        except SQLAlchemyError as e:
            self.logger.error(f"Erro ao conectar com o banco de dados: {str(e)}")
