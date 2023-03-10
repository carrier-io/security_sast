from typing import Union

from flask import request
from flask_restful import Resource
from pylon.core.tools import log

from ...utils import run_test, parse_test_data
from ...models.tests import SecurityTestsSAST


class API(Resource):
    url_params = [
        '<int:project_id>/<int:test_id>',
        '<int:project_id>/<string:test_id>',
    ]

    def __init__(self, module):
        self.module = module

    def put(self, project_id: int, test_id: Union[int, str]):
        """ Update test data """
        run_test_ = request.json.pop('run_test', False)
        test_data, errors = parse_test_data(
            project_id=project_id,
            request_data=request.json,
            rpc=self.module.context.rpc_manager,
            common_kwargs={'exclude': {'test_uid', }}
        )

        if errors:
            return errors, 400

        test_query = SecurityTestsSAST.query.filter(SecurityTestsSAST.get_api_filter(project_id, test_id))
        schedules = test_data.pop('scheduling', [])
        test_query.update(test_data)
        SecurityTestsSAST.commit()
        test = test_query.one()

        test.handle_change_schedules(schedules)

        if run_test_:
            resp = run_test(test)
            return resp, resp.get('code', 200)

        return test.to_json(), 200

    def post(self, project_id: int, test_id: Union[int, str]):
        """ Run test """
        test = SecurityTestsSAST.query.filter(
            SecurityTestsSAST.get_api_filter(project_id, test_id)
        ).first()
        if not test:
            return {"ok": False, "error": "Test is not found"}, 404
        resp = run_test(test, config_only=request.json.get('type', False))
        return resp, resp.get('code', 200)
