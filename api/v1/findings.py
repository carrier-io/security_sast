import hashlib

from flask import request, abort, make_response
from flask_restful import Resource
from sqlalchemy import and_, or_, asc

from ...models.reports import SecurityReport
from ...models.details import SecurityDetails
from ...models.results import SecurityResultsSAST
from pylon.core.tools import log  # pylint: disable=E0611,E0401


class API(Resource):
    url_params = [
        '<int:project_id>',
        '<int:project_id>/<int:test_id>',
    ]

    def __init__(self, module):
        self.module = module

    def _calcualte_limit(self, limit, total):
        return total if limit == 'All' or limit == 0 else limit

    def get(self, project_id: int, test_id: int):
        args = request.args
        limit_ = args.get("limit")
        offset_ = args.get("offset")

        filter_ = [
            SecurityReport.project_id == project_id,
            SecurityReport.report_id == test_id
        ]

        if args.get("status"):
            filter_.append(SecurityReport.status.ilike(args["status"]))

        # sorting
        if args.get("sort"):
            sort_rule = getattr(getattr(SecurityReport, args["sort"]), args["order"])()
        else:
            sort_rule = SecurityReport.id.desc()

        total = SecurityReport.query.filter(*filter_).count()
        issues = SecurityReport.query.filter(*filter_).order_by(sort_rule)\
                .limit(self._calcualte_limit(limit_, total))\
                .offset(offset_)

        results = []
        for issue in issues:
            _res = issue.to_json()
            _res["details"] = SecurityDetails.query.filter_by(id=_res["details"]).first().details
            results.append(_res)
        return {"total": total, "rows": results}, 200



    def put(self, project_id: int, test_id: int):
        args = request.json
        issues = args.get('issues_id')
        issue_hashes = args.get('issue_hashes')
        accept_message = {"message": "accepted"}

        assert issues or issue_hashes, abort(400, data={"message": "No issues provided"})

        if args.get("severity"):
            update_value = {"severity": args["severity"].replace(" ", "_")}
        elif args.get("status"):
            update_value = {"status": args["status"].replace(" ", "_")}
        else:
            abort(400, data={"message": "Action is invalid"})

        if issues:
            issue_hashes.extend(
                SecurityReport.query.filter(
                    SecurityReport.project_id == project_id,
                    SecurityReport.report_id == test_id,
                    SecurityReport.id.in_(issues),
                ).values('issue_hash', flat=True)
            )

        SecurityReport.query.filter(
            SecurityReport.report_id == test_id,
            SecurityReport.project_id == project_id,
            SecurityReport.issue_hash.in_(set(issue_hashes)),
        ).update(update_value)
        SecurityReport.commit()

        results = SecurityResultsSAST.query.filter(
            and_(
                SecurityResultsSAST.project_id == project_id,
                SecurityResultsSAST.id == test_id
            )
        ).first()

        if args.get("status"):
            results.update_status_counts()

        if args.get("severity"):
            results.update_severity_counts()

        results.update_findings_counts()
        return make_response(accept_message, 204)

    def post(self, project_id: int, *args, **kvargs):
        finding_db = None
        log.info(request.json)
        for finding in request.json:
            md5 = hashlib.md5(finding["details"].encode("utf-8")).hexdigest()
            hash_id = SecurityDetails.query.filter(
                and_(SecurityDetails.project_id == project_id, SecurityDetails.detail_hash == md5)
            ).first()
            if not hash_id:
                hash_id = SecurityDetails(detail_hash=md5, project_id=project_id, details=finding["details"])
                hash_id.insert()
            # Verify issue is false_positive or ignored
            finding["details"] = hash_id.id
            finding['project_id'] = project_id
            # finding['report_id'] = test_id

            entrypoints = ""
            for endpoint in finding.get("endpoints", []):
                if isinstance(endpoint, list):
                    entrypoints += "<br />".join(endpoint)
                else:
                    entrypoints += f"<br />{endpoint}"
            finding["endpoints"] = entrypoints

            issue = SecurityReport.query.filter(and_(
                SecurityReport.project_id == project_id,
                SecurityReport.issue_hash == finding['issue_hash'])).first()
            if issue:
                finding['severity'] = issue.severity
            if not (finding.get("false_positive") == 1 or finding.get("excluded_finding") == 1):
                # todo: query sum from db?
                issues = SecurityReport.query.filter(
                    and_(SecurityReport.project_id == project_id,
                         SecurityReport.issue_hash == finding["issue_hash"],
                         or_(SecurityReport.status == "False_Positive",
                             SecurityReport.status == "Ignored")
                         )).all()
                false_positive = sum([1 for issue in issues if issue.status == "False_Positive"])
                excluded_finding = sum([1 for issue in issues if issue.status == "Ignored"])

                finding["status"] = "False_Positive" if false_positive > 0 else "Not_defined"
                finding["status"] = "Ignored" if excluded_finding > 0 else "Not_defined"

                # TODO: wrap this to try-except or delete from requests
                for k in ['false_positive', 'excluded_finding', 'info_finding']:
                    try:
                        del finding[k]
                    except KeyError:
                        pass
            finding_db = SecurityReport(**finding)
            finding_db.add()
            # print('POSTED', finding_db)

        if finding_db:
            finding_db.commit()
            return make_response('ok', 204)
        return make_response('No findings passed', 400)
