from sqlalchemy import String, Column, Integer, Text
from tools import db_tools, db

import sqlalchemy.types as types


class ChoiceType(types.TypeDecorator):

    impl = types.String
    cache_ok = False

    def __init__(self, choices: dict, **kwargs):
        self.choices = dict(choices)
        super().__init__(**kwargs)

    def process_bind_param(self, value: str, dialect):
        return self.choices[value.lower()]

    def process_result_value(self, value: str, dialect):
        try:
            return self.choices[value.lower()]
        except KeyError:
            return [k for k, v in self.choices.items() if v.lower() == value.lower()][0]


class SecurityReport(db_tools.AbstractBaseMixin, db.Base):

    SEVERITY_CHOICES = {
        'critical': 'critical',
        'high': 'high',
        'medium': 'medium',
        'low': 'low',
        'info': 'info',
    }
    STATUS_CHOICES = {
        'valid': 'valid',
        'false_positive': 'false positive',
        'ignored': 'ignored',
        'not_defined': 'not defined'
    }

    __tablename__ = "security_sast_report"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    report_id = Column(Integer, nullable=False)
    issue_hash = Column(String(128), unique=False)
    tool_name = Column(String(128), unique=False)
    description = Column(Text, unique=False)
    severity = Column(ChoiceType(SEVERITY_CHOICES), unique=False)
    details = Column(Integer, unique=False)
    endpoints = Column(Text, unique=False)
    status = Column(ChoiceType(STATUS_CHOICES), unique=False, default='not_defined')

    # TODO: delete rows below if needed
    false_positive = Column(Integer, unique=False)
    info_finding = Column(Integer, unique=False)
    excluded_finding = Column(Integer, unique=False)

    def to_json(self, exclude_fields: tuple = ()) -> dict:
        result = super().to_json()
        for col in ('status', 'severity'):
            result[col] = result[col].replace('_', ' ')
        return result