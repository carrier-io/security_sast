from ..models.thresholds import SecurityThresholds
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields


class SecurityThresholdsSchema(SQLAlchemyAutoSchema):
    test_name = fields.Str(attribute='name')
    test_scope = fields.Str(attribute='description')

    class Meta:
        model = SecurityThresholds
        fields = (
            'id',
            'project_id',
            'test_uid',
            'test_name',
            'test_scope',
            'params',
        )


threshold_schema = SecurityThresholdsSchema()
thresholds_schema = SecurityThresholdsSchema(many=True)
