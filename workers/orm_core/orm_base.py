from typing import List, Dict, Any

from sqlalchemy import create_engine, inspect, MetaData
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

from settings import DatabaseConfig
from utils.model.model_table_creator import Base
from utils.enum_config import TableRecord


class ORMWorker():
    def __init__(self, connection_info=DatabaseConfig.OUTPUT_ENGINE_INFO,
                 auto_flush=False, echo=False, **kwargs):
        self.connection_info = connection_info
        self.base = Base
        self.engine = create_engine(self.connection_info, echo=echo, **kwargs)
        self.create_table_cls()
        self.session = Session(self.engine, autoflush=auto_flush)
        self.table_name_list = [item.value for item in TableRecord]
        self.table_cls_dict = self.table_cls_maker(self.table_name_list)

    def __str__(self):
        return f"table class object : {','.join(list(self.table_cls_dict.keys()))}"

    def dispose(self):
        self.close_session()
        self.engine.dispose()

    def close_session(self):
        self.session.close()

    def show_tables(self):
        inspector = inspect(self.engine)
        show_table = inspector.get_table_names()
        return show_table

    def orm_cls_to_dict(self, record) -> Dict[str, Any]:
        return {c.name: getattr(record, c.name, None) for c in record.__table__.columns}

    def create_table_cls(self):
        tables = [item.value for item in TableRecord]
        show_table = self.show_tables()
        if not set(tables).issubset(show_table):
            self.base.metadata.create_all(self.engine, checkfirst=True)

    def table_cls_maker(self, table_attr: List[str]) -> Dict:
        meta = MetaData()
        meta.reflect(self.engine, only=table_attr)
        Base = automap_base(metadata=meta)
        Base.prepare()
        # build table cls
        return {i: getattr(Base.classes, i) for i in table_attr}
