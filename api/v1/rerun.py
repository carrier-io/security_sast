from flask import make_response
from flask_restful import Resource

from ...models.tests import SecurityTestsSAST
from ...utils import run_test


class API(Resource):
    url_params = [
        '<int:security_results_sast_id>',
    ]

    def __init__(self, module):
        self.module = module

    def post(self, security_results_sast_id: int):
        """
        Post method for re-running test
        """

        test_result = self.module.results_or_404(security_results_sast_id)
        test_config = test_result.test_config

        test = SecurityTestsSAST.query.get(test_config['id'])
        if not test:
            test = SecurityTestsSAST(
                project_id=test_config['project_id'],
                project_name=test_config['project_name'],
                test_uid=test_config['test_uid'],
                name=test_config['name'],
                description=test_config['description'],
                urls_to_scan=test_config['urls_to_scan'],
                urls_exclusions=test_config['urls_exclusions'],
                scan_location=test_config['scan_location'],
                test_parameters=test_config['test_parameters'],
                integrations=test_config['integrations'],
            )
            test.insert()

        resp = run_test(test)
        return make_response(resp, resp.get('code', 200))
