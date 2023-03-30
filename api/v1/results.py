from flask import make_response, request
from flask_restful import Resource

from tools import api_tools

from ...models.results import SecurityResultsSAST


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        args = request.args
        reports = []
        total, res = api_tools.get(project_id, args, SecurityResultsSAST)
        for each in res:
            reports.append(each.to_json())
        return make_response({"total": total, "rows": reports}, 200)


    def delete(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        try:
            delete_ids = list(map(int, request.args["id[]"].split(',')))
        except TypeError:
            return make_response('IDs must be integers', 400)
        SecurityResultsSAST.query.filter(
            SecurityResultsSAST.project_id == project.id,
            SecurityResultsSAST.id.in_(delete_ids)
        ).delete()
        SecurityResultsSAST.commit()
        return {"message": "deleted"}, 204
