from sqlalchemy import and_, exc
from flask import request
from flask_restful import Resource

from pydantic import ValidationError

from ...models.thresholds import SecurityThresholds
from ...models.tests import SecurityTestsSAST
from ...models.pd.thresholds import ThresholdPD
from ...serializers.thresholds import thresholds_schema

from tools import api_tools, db
from pylon.core.tools import log  # pylint: disable=E0611,E0401


class API(Resource):
    url_params = [
        '<int:project_id>',
        '<int:project_id>/<int:threshold_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        fields = (
            SecurityThresholds.id, SecurityThresholds.project_id, 
            SecurityThresholds.test_uid, SecurityThresholds.project_id,
            SecurityThresholds.params,
            SecurityTestsSAST.name, SecurityTestsSAST.description
        )
        on_clause = and_(SecurityTestsSAST.test_uid == SecurityThresholds.test_uid, 
            SecurityThresholds.project_id == project.id)
        query = db.session.query(*fields).join(SecurityTestsSAST, on_clause)
        # filter condition here
        query = query
        # total count
        total = query.count()
        # making query
        result = query.all()
        result = thresholds_schema.dump(result)
        return {'total': total, 'rows': result}, 200

    def post(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        try:
            pd_obj = ThresholdPD(project_id=project.id, **request.json)
        except ValidationError as e:
            return e.errors(), 400
        try:
            th = SecurityThresholds(**pd_obj.dict())
            th.insert()
        except exc.IntegrityError as e:
            return {'ok': False, "error": "Threshold for this test already exists"}, 400
        return th.to_json(), 201

    def delete(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        try:
            delete_ids = list(map(int, request.args["id[]"].split(',')))
        except TypeError:
            return 'IDs must be integers', 400

        filter_ = and_(
            SecurityThresholds.project_id == project.id,
            SecurityThresholds.id.in_(delete_ids)
        )
        SecurityThresholds.query.filter(
            filter_
        ).delete()
        SecurityThresholds.commit()
        return {'ids': delete_ids}, 204

    def put(self, project_id: int, threshold_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        try:
            pd_obj = ThresholdPD(project_id=project.id, **request.json)
        except ValidationError as e:
            return e.errors(), 400
        th_query = SecurityThresholds.query.filter(
            SecurityThresholds.project_id == project.id,
            SecurityThresholds.id == threshold_id
        )
        th_query.update(pd_obj.dict())
        SecurityThresholds.commit()
        return th_query.one().to_json(), 200