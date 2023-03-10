import json
from queue import Empty
from typing import Tuple, Union
from pydantic import ValidationError

from pylon.core.tools import log

from .models.tests import SecurityTestsSAST
from .models.results import SecurityResultsSAST
from uuid import uuid4
from tools import rpc_tools, task_tools


def run_test(test: SecurityTestsSAST, config_only=False) -> dict:
    engagement_id = test.integrations.get('reporters', {}).get('reporter_engagement')

    results = SecurityResultsSAST(
        project_id=test.project_id,
        test_id=test.id,
        test_uid=test.test_uid,
        build_id=f'build_{uuid4()}',
        test_name=test.name,
        engagement=engagement_id
    )
    results.insert()

    test.results_test_id = results.id
    test.build_id = results.build_id
    test.commit()

    event = [test.configure_execution_json("cc")]

    if config_only:
        return event[0]
    
    resp = task_tools.run_task(test.project_id, event)
    resp['redirect'] = f'/task/{resp["task_id"]}/results'  # todo: where this should lead to?

    test.rpc.call.increment_statistics(test.project_id, 'sast_scans')

    resp['result_id'] = results.id
    return resp


class ValidationErrorPD(Exception):
    def __init__(self, loc: Union[str, list], msg: str):
        self.loc = [loc] if isinstance(loc, str) else loc
        self.msg = msg
        super().__init__({'loc': self.loc, 'msg': msg})

    def json(self):
        return json.dumps(self.dict())

    def dict(self):
        return {'loc': self.loc, 'msg': self.msg}


def parse_test_data(project_id: int, request_data: dict,
                    *,
                    rpc=None, common_kwargs: dict = None,
                    test_create_rpc_kwargs: dict = None,
                    raise_immediately: bool = False,
                    skip_validation_if_undefined: bool = True,
                    ) -> Tuple[dict, list]:
    """
    Parses data while creating test

    :param project_id: Project id
    :param request_data: data from request json to validate
    :param rpc: instance of rpc_manager or None(will be initialized)
    :param common_kwargs: kwargs for common_test_parameters
            (test parameters apart from test_params table. E.g. name, description)
    :param test_create_rpc_kwargs: for each test_data key a rpc is called - these kwargs will be passed to rpc call
    :param raise_immediately: weather to raise validation error on first encounter or raise after collecting all errors
    :param skip_validation_if_undefined: if no rpc to validate test_data key is found
            data will remain untouched if True or erased if False
    :return:
    """
    if not rpc:
        rpc = rpc_tools.RpcMixin().rpc

    common_kwargs = common_kwargs or dict()
    test_create_rpc_kwargs = test_create_rpc_kwargs or dict()

    errors = list()

    test_name = request_data.pop('name', None)
    test_description = request_data.pop('description', None)
    source = request_data.pop('source', None)

    try:
        test_data = rpc.call.security_sast_test_create_common_parameters(
            project_id=project_id,
            name=test_name,
            description=test_description,
            source=source,
            **common_kwargs
        )
    except ValidationError as e:
        test_data = dict()
        errors.extend(e.errors())
        if raise_immediately:
            return test_data, errors

    for k, v in request_data.items():
        try:
            # log.info(f'security test create :: parsing :: [{k}]')
            test_data.update(rpc.call_function_with_timeout(
                func=f'security_sast_test_create_{k}',
                timeout=2,
                data=v,
                **test_create_rpc_kwargs
            ))
        except Empty:
            log.warning(f'Cannot find parser for {k}')
            if skip_validation_if_undefined:
                test_data.update({k: v})
        except ValidationError as e:
            for i in e.errors():
                i['loc'] = [k, *i['loc']]
            errors.extend(e.errors())

            if raise_immediately:
                return test_data, errors
        except Exception as e:
            log.warning(f'Exception as e {type(e)}')
            e.loc = [k, *getattr(e, 'loc', [])]
            errors.append(ValidationErrorPD(e.loc, str(e)))
            if raise_immediately:
                return test_data, errors

    return test_data, errors
