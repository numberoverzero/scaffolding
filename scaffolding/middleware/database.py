import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker


# noinspection PyShadowingNames
class Database:
    def __init__(self, autocommit=True) -> None:
        self.base = declarative_base()
        self.engine = None
        self.session = scoped_session(sessionmaker())
        self.autocommit = autocommit

    def init(self, connection_url: str, echo=True, create_tables=True) -> None:
        self.engine = sqlalchemy.create_engine(connection_url, echo=echo)
        self.base.metadata.bind = self.engine
        self.session.configure(bind=self.engine)
        if create_tables:
            self.base.metadata.create_all(self.engine)

    def create_middleware(self) -> "DatabaseMiddleware":
        return DatabaseMiddleware(self)


class DatabaseMiddleware:
    def __init__(self, db: Database) -> None:
        self.db = db

    def process_response(self, *_, req_succeeded: bool, **__) -> None:
        try:
            if self.db.autocommit:
                if req_succeeded:
                    self.db.session.commit()
                else:
                    self.db.session.rollback()
        finally:
            self.db.session.remove()
