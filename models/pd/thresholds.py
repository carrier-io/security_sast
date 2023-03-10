from pydantic import BaseModel, validator
from typing import List
from ...models.tests import SecurityTestsSAST


class ThresholdParams(BaseModel):
    name: str
    comparison: str
    value: int

    __name_choices = (
        'critical', 
        'high',
        'medium',
        'low',
        'info',
        'errors'
    )

    @validator('name')
    def validate_name(cls, value:str, values:dict):
        assert value.lower() in  cls.__name_choices, f"Invalid param name - {value}"
        return value.lower()

    @validator('comparison')
    def validate_comparison(cls, value: str):
        assert value in {'gte', 'lte', 'lt', 'gt', 'eq'}, f'Comparison {value} is not supported'
        return value


class ThresholdPD(BaseModel):
    project_id: int
    test_uid: str
    params: List[ThresholdParams]

    @validator('test_uid')
    def validate_test_exists(cls, value: str, values: dict):
        assert SecurityTestsSAST.query.filter(
            SecurityTestsSAST.project_id == values['project_id'],
            SecurityTestsSAST.test_uid == value
        ).first(), f'Test with name {value} does not exist'
        return value