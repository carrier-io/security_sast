from flask_restful import Resource
from sqlalchemy import and_

# from ...shared.utils.restApi import RestResource
# from ...shared.utils.api_utils import build_req_parser

from ...models.tests import SecurityTestsSAST
from ...models.thresholds import SecurityThresholds
from flask import request, make_response
from pylon.core.tools import log  # pylint: disable=E0611,E0401


class API(Resource):
    url_params = [
        '<int:project_id>/<string:seed>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int, seed: str):
        """ Get config for seed """
        args = request.args
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)

        test_type = seed.split("_")[0]
        test_id = seed.split("_")[1]

        if test_type == "sast":
            _filter = and_(
                SecurityTestsSAST.project_id == project.id,
                SecurityTestsSAST.test_uid == test_id
            )
            test = SecurityTestsSAST.query.filter(_filter).first()
            try:
                thresholds = SecurityThresholds.query.filter(
                    SecurityThresholds.test_uid == test_id
                ).first().to_json(
                    exclude_fields=("id", "project_id", "test_name", "test_uid")
                )
                log.info(thresholds)
                thresholds = thresholds['params']
            except AttributeError:
                thresholds = {}
            return test.configure_execution_json(args.get("type"), thresholds=thresholds)
        return make_response(f'Unknown test type {test_type}', 400)
