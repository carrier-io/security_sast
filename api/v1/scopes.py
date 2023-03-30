from flask import request
from flask_restful import Resource
from sqlalchemy import and_

from ...models.tests import SecurityTestsSAST


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        query_result = SecurityTestsSAST.query.with_entities(SecurityTestsSAST.description).filter(
            SecurityTestsSAST.name == request.args.get("name"),
            SecurityTestsSAST.project_id == project.id
        ).distinct(SecurityTestsSAST.description).all()
        return [i[0] for i in query_result], 200