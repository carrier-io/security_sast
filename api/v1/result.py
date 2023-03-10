from datetime import datetime

from flask import make_response, request
from flask_restful import Resource
from pylon.core.tools import log  # pylint: disable=E0611,E0401

from ...models.results import SecurityResultsSAST


class API(Resource):
    url_params = [
        '<int:project_id>/<int:result_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int, result_id: int):
        obj = SecurityResultsSAST.query.filter(
            SecurityResultsSAST.project_id == project_id,
            SecurityResultsSAST.id == result_id,
        ).one()
        return obj.to_json(), 200

    def post(self, project_id: int, result_id: int):
        args = request.json
        self.module.context.rpc_manager.call.project_get_or_404(project_id)

        # TODO move sast/dast quota checks to a new endpoint, which will be triggered before the scan
        if not self.module.context.rpc_manager.call.project_check_quota(project_id, 'sast_scans'):
            return make_response(
                {"Forbidden": "The number of sast scans allowed in the project has been exceeded"},
                400
            )

        # security results getter
        report = SecurityResultsSAST.query.filter(
            SecurityResultsSAST.project_id == project_id,
            SecurityResultsSAST.id == result_id,
        ).one()

        upd = dict(
            scan_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            # project_id=project.id,
            scan_duration=args["scan_time"],
            # project_name=args["project_name"],
            app_name=args["app_name"],
            dast_target=args["dast_target"],
            sast_code=args["sast_code"],
            scan_type=args["scan_type"],
            findings=args["findings"] - (args["false_positives"] + args["excluded"]),
            false_positives=args["false_positives"],
            excluded=args["excluded"],
            info_findings=args["info_findings"],
            environment=args["environment"]
        )

        for k, v in upd.items():
            setattr(report, k, v)

        report.commit()

        if args["scan_type"].lower() == 'sast':
            self.module.context.rpc_manager.call.increment_statistics(project_id, 'sast_scans')
        elif args["scan_type"].lower() == 'dast':
            self.module.context.rpc_manager.call.increment_statistics(project_id, 'dast_scans')

        return make_response({"id": report.id}, 200)
