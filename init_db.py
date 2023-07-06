from tools import db


def init_db():
    from .models.tests import SecurityTestsSAST
    from .models.results import SecurityResultsSAST
    from .models.thresholds import SecurityThresholds
    from .models.details import SecurityDetails
    from .models.reports import SecurityReport
    db.get_shared_metadata().create_all(bind=db.engine)
