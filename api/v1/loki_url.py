import json
import gzip

import flask
from flask import make_response
from flask_restful import Resource
from pylon.core.tools import log
from pylon.core.seeds.minio import MinIOHelper
from ....shared.tools.constants import APP_HOST
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

        build_id = SecurityResultsSAST.query.get_or_404(result_key).build_id

        websocket_base_url = APP_HOST.replace("http://", "ws://").replace("https://", "wss://")
        websocket_base_url += "/loki/api/v1/tail"
        logs_query = "{" + f'report_id="{result_key}",project="{project_id}",build_id="{build_id}"' + "}"

        logs_start = 0
        logs_limit = 10000000000

        return make_response(
            {"websocket_url": f"{websocket_base_url}?query={logs_query}&start={logs_start}&limit={logs_limit}"},
            200
        )
