from flask import request
from flask_restful import Resource
from sqlalchemy import and_

from ...models.tests import SecurityTestsSAST


class API(Resource):
    url_params = [
        '<int:project_id>/<string:name>/<string:scope>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int, name: str, scope: str):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        query_result = SecurityTestsSAST.query.with_entities(SecurityTestsSAST.test_uid).filter(
            SecurityTestsSAST.name == name,
            SecurityTestsSAST.project_id == project.id,
            SecurityTestsSAST.description == scope,
        ).first()
        return query_result[0], 200