import flask
from flask import make_response
from flask_restful import Resource
from tools import LokiLogFetcher
from ...models.results import SecurityResultsSAST


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        result_key = flask.request.args.get("result_id", None)
        if not result_key:  # or key not in state:
            return make_response({"message": ""}, 404)

        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        build_id = SecurityResultsSAST.query.get_or_404(result_key).build_id

        use_sio_logs = self.module.descriptor.config.get("use_sio_logs", False)

        if use_sio_logs:
            return make_response(
                {"labels": {
                    "project": f"{project_id}",
                    "report_id": f"{result_key}",
                    "build_id": f"{build_id}",
                }},
                200
            )

        websocket_base_url = LokiLogFetcher.from_project(project).get_websocket_url(project)

        logs_start = 0
        logs_limit = 10000000000
        logs_query = "{" + f'report_id="{result_key}",project="{project_id}",build_id="{build_id}"' + "}"

        return make_response(
            {"websocket_url": f"{websocket_base_url}?query={logs_query}&start={logs_start}&limit={logs_limit}"},
            200
        )
