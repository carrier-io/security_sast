from sqlalchemy import String, Column, Integer, JSON
from tools import db_tools, db
from ..models.tests import SecurityTestsSAST


class SecurityThresholds(db_tools.AbstractBaseMixin, db.Base):
    __tablename__ = "sec_sast_thresholds"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    test_uid = Column(String, unique=True, nullable=False)
    params = Column(JSON, nullable=False)