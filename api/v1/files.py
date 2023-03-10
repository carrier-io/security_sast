import uuid
from flask_restful import Resource
from flask import request
from tools import api_tools
from pylon.core.tools import log  # pylint: disable=E0611,E0401


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        return {}, 200

    def post(self, project_id: int):
        file = request.files.get("file")
        bucket_name = request.args.get('bucket')
        if not file:
            return {"ok":False, "error": "Empty payload"}, 400

        bucket_name = bucket_name if bucket_name else "code-test-" + uuid.uuid4().hex
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        api_tools.upload_file(bucket_name, file, project, create_if_not_exists=True)
        meta = {
            'bucket': bucket_name, 
            'filename': file.filename, 
            'project_id': project_id
        }
        return {"ok":True, "item":meta}, 201
    
    def delete(self, project_id: int):
        return {}, 204