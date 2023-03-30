from typing import Optional, List
from uuid import uuid4
from pydantic import BaseModel, validator, AnyUrl, root_validator

from ....shared.models.pd.test_parameters import TestParameter, TestParamsBase  # todo: workaround for this import
from pylon.core.tools import log
from tools import rpc_tools


_required_params = set()



class SecurityTestParam(TestParameter):
    """
    Each ROW of test_params table
    """

    class Config:
        anystr_strip_whitespace = True
        anystr_lower = True

    _required_params = _required_params


class SecurityTestParams(TestParamsBase):
    """
    Base case class for security test.
    Used as a parent class for actual security test model
    """

    class Config:
        anystr_strip_whitespace = True
        anystr_lower = True

    _required_params = _required_params

    # the following fields are optional as they are set in validator using _test_params_mapping
    scan_location: Optional[str] = ''
    test_parameters: List[SecurityTestParam]

    @validator('scan_location', always=True)
    def set_values_from_test_params(cls, value, values, field):
        if value and value != field.default:
            return value
        _test_params_mapping = {
            'scan location': 'scan_location',
            'scan_location': 'scan location',
        }

        mapped_name = _test_params_mapping.get(field.name)
        if mapped_name:
            try:
                return [i.default for i in values['test_parameters'] if i.name == mapped_name][0]
            except (IndexError, KeyError):
                ...

        return value

    @root_validator(pre=True)
    def make_lowercase(cls, values):
        for i in values.get('test_parameters', []):
            for field in ['name', 'type']:
                val = i.get(field)
                if val:
                    i[field] = str(val).lower()
        return values


class SecurityTestCommon(BaseModel):
    """
    Model of test itself without test_params or other plugin module's data
    """

    project_id: int
    project_name: str
    test_uid: Optional[str]
    name: str
    description: str
    source: dict

    @root_validator
    def set_uuid(cls, values):
        if not values.get('test_uid'):
            values['test_uid'] = str(uuid4())
        return values

    @root_validator(pre=True, allow_reuse=True)
    def empty_str_to_none(cls, values):
        removed = []
        for k in list(values.keys()):
            if values[k] == '':
                removed.append(k)
                del values[k]
        return values

    @validator('source')
    def validate_sources(cls, value: dict, values):
        validated = rpc_tools.RpcMixin().rpc.call.parse_source(value)
        return {
            'name': value['name'],
            **validated.dict()
        }

