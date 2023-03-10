#     Copyright 2021 getcarrier.io
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from json import dumps
from queue import Empty
from typing import List, Union
from sqlalchemy import Column, Integer, String, ARRAY, JSON, and_
from tools import rpc_tools, db, db_tools, constants, secrets_tools
from pylon.core.tools import log  # pylint: disable=E0611,E0401


class SecurityTestsSAST(db_tools.AbstractBaseMixin, db.Base, rpc_tools.RpcMixin):
    """ Security Tests: SAST """
    __tablename__ = "security_tests_sast"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    project_name = Column(String(64), nullable=False)
    test_uid = Column(String(64), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(String(256), nullable=True, unique=False)
    test_parameters = Column(ARRAY(JSON), nullable=True)
    integrations = Column(JSON, nullable=True)
    schedules = Column(ARRAY(Integer), nullable=True, default=[])
    results_test_id = Column(Integer)
    build_id = Column(String(128), unique=True)
    scan_location = Column(String(128), nullable=False)
    source = Column(JSON, nullable=False)


    def handle_change_schedules(self, schedules_data: List[dict]):
        new_schedules_ids = set(i['id'] for i in schedules_data if i['id'])
        ids_to_delete = set(self.schedules).difference(new_schedules_ids)
        self.schedules = []
        for s in schedules_data:
            log.warning('!!!adding schedule')
            log.warning(s)
            self.add_schedule(s, commit_immediately=False)
        try:
            self.rpc.timeout(2).scheduling_delete_schedules(ids_to_delete)
        except Empty:
            ...
        self.commit()


    @property
    def scanners(self) -> list:
        try:
            return list(self.integrations.get('scanners', {}).keys())
        except AttributeError:
            return []


    @staticmethod
    def get_api_filter(project_id: int, test_id: Union[int, str]):
        log.info(f'getting filter int? {isinstance(test_id, int)}  {test_id}')
        if isinstance(test_id, int):
            return and_(
                SecurityTestsSAST.project_id == project_id,
                SecurityTestsSAST.id == test_id
            )
        return and_(
            SecurityTestsSAST.project_id == project_id,
            SecurityTestsSAST.test_uid == test_id
        )


    def configure_execution_json(self, output="cc", execution=False, thresholds={}):
        """ Create configuration for execution """
        #
        if output == "dusty":
            #
            from flask import current_app
            global_sast_settings = dict()
            global_sast_settings["max_concurrent_scanners"] = 1
            loki_settings = current_app.config["CONTEXT"].settings["loki"]

            if "git_" in self.source.get("name"):
                actions_config = {
                    "git_clone": {
                        "source": self.source.get("repo"),
                        "branch": self.source.get("branch"),
                        "target": "/tmp/code"
                    }
                }

                if self.source.get("name") == "git_https":
                    if self.source.get("username") != "":
                        actions_config["git_clone"]["username"] = secrets_tools.unsecret(self.source.get("username"), project_id=self.project_id)
                    if self.source.get("password") != "":
                        actions_config["git_clone"]["password"] = secrets_tools.unsecret(self.source.get("password"), project_id=self.project_id)

                if self.source.get("name") == "git_ssh":
                    secret_value = secrets_tools.unsecret(self.source.get("private_key"), project_id=self.project_id)
                    actions_config["git_clone"]["key_data"] = secret_value.replace("\n", "|")
                    actions_config["git_clone"]["password"] = secrets_tools.unsecret(self.source.get("password"), project_id=self.project_id)


            if self.source.get("name") == "artifact":
                actions_config = {
                    "galloper_artifact": {
                        "bucket": self.source.get("file_meta", {}).get("bucket", None),
                        "object": self.source.get("file_meta", {}).get("filename", None),
                        "target": "/tmp/code",
                        "delete": False
                    } 
                }
            
            if self.source.get("name") == "local":
                actions_config = {
                    "galloper_artifact": {
                        "bucket": "sast",
                        "object": f"{self.build_id}.zip",
                        "target": "/tmp/code",
                        "delete": False
                    }
                }
            
            if self.source.get("name") == "container":
                actions_config = {
                    "container_metadata": {
                        "image_name": self.source.get('image_name'),
                    }
                }
            #
            # Scanners
            #
            scanners_config = dict()
            for scanner_name in self.integrations.get('scanners', []):
                try:
                    config_name, config_data = \
                        self.rpc.call_function_with_timeout(
                            func=f'dusty_config_{scanner_name}',
                            timeout=2,
                            context=None,
                            test_params=self.__dict__,
                            scanner_params=self.integrations["scanners"][scanner_name],
                        )
                    scanners_config[config_name] = config_data
                except Empty:
                    log.warning(f'Cannot find scanner config rpc for {scanner_name}')

            #
            # Processing
            #
            processing_config = dict()
            for processor_name in self.integrations.get("processing", []):
                try:
                    config_name, config_data = \
                        self.rpc.call_function_with_timeout(
                            func=f"dusty_config_{processor_name}",
                            timeout=2,
                            context=None,
                            test_params=self.__dict__,
                            scanner_params=self.integrations["processing"][processor_name],
                        )
                    processing_config[config_name] = config_data
                except Empty:
                    log.warning(f'Cannot find processor config rpc for {processor_name}')


            tholds = {}    
            for threshold in thresholds:
                if int(threshold['value']) > -1:
                    tholds[threshold['name'].capitalize()] = {
                        'comparison': threshold['comparison'],
                        'value': int(threshold['value']),
                    }

            processing_config["quality_gate_sast"] = {
                "thresholds": tholds
            }
        
            #
            # Reporters
            #
            reporters_config = dict()
            for reporter_name in self.integrations.get('reporters', []):
                try:
                    config_name, config_data = \
                        self.rpc.call_function_with_timeout(
                            func=f'dusty_config_{reporter_name}',
                            timeout=2,
                            context=None,
                            test_params=self.__dict__,
                            scanner_params=self.integrations["reporters"][reporter_name],
                        )
                    reporters_config[config_name] = config_data
                except Empty:
                    log.warning(f'Cannot find reporter config rpc for {reporter_name}')


            reporters_config["centry_loki"] = {
                "url": loki_settings["url"],
                "labels": {
                    "project": str(self.project_id),
                    "build_id": str(self.build_id),
                    "report_id": str(self.results_test_id),
                    "hostname": "dusty"
                },
            }
            reporters_config["centry_status"] = {
                "url": secrets_tools.unsecret(
                    "{{secret.galloper_url}}",
                    project_id=self.project_id
                ),
                "token": secrets_tools.unsecret(
                    "{{secret.auth_token}}",
                    project_id=self.project_id
                ),
                "project_id": str(self.project_id),
                "test_id": str(self.results_test_id),
            }

            reporters_config["centry"] = {
                "url": secrets_tools.unsecret(
                    "{{secret.galloper_url}}",
                    project_id=self.project_id
                ),
                "token": secrets_tools.unsecret(
                    "{{secret.auth_token}}",
                    project_id=self.project_id
                ),
                "project_id": str(self.project_id),
                "test_id": str(self.results_test_id),
            }

            dusty_config = {
                "config_version": 2,
                "suites": {
                    "sast": {
                        "settings": {
                            "project_name": self.project_name,
                            "project_description": self.name,
                            "environment_name": "target",
                            "testing_type": "SAST",
                            "scan_type": "full",
                            "build_id": self.test_uid,
                            "sast": global_sast_settings
                        },
                        "actions": actions_config,
                        "scanners": {
                            "sast": scanners_config
                        },
                        "processing": processing_config,
                        "reporters": reporters_config
                    }
                }
            }
            #
            return dusty_config
        #
        job_type = "sast"
        # container = f"getcarrier/{job_type}:{CURRENT_RELEASE}"
        container = f"getcarrier/sast_local"
        parameters = {
            "cmd": f"run -b centry:{job_type}_{self.test_uid} -s {job_type}",
            "GALLOPER_URL": secrets_tools.unsecret(
                "{{secret.galloper_url}}",
                project_id=self.project_id
            ),
            "GALLOPER_PROJECT_ID": f"{self.project_id}",
            "GALLOPER_AUTH_TOKEN": secrets_tools.unsecret(
                "{{secret.auth_token}}",
                project_id=self.project_id
            ),
        }
        if self.source.get("name") == "local":
            parameters["code_path"] = self.source.get("path")

        cc_env_vars = {
            "RABBIT_HOST": secrets_tools.unsecret(
                "{{secret.rabbit_host}}",
                project_id=self.project_id
            ),
            "RABBIT_USER": secrets_tools.unsecret(
                "{{secret.rabbit_user}}",
                project_id=self.project_id
            ),
            "RABBIT_PASSWORD": secrets_tools.unsecret(
                "{{secret.rabbit_password}}",
                project_id=self.project_id
            ),
            "REPORT_ID": str(self.results_test_id),
            "build_id": str(self.build_id),
            "project_id": str(self.project_id),
        }
        concurrency = 1
        #
        if output == "docker":
            docker_run = f"docker run --rm -i -t"
            if self.source.get('name') == 'local':
                docker_run = f"docker run --rm -i -t -v \"{self.source.get('path')}:/code\""
            return f"{docker_run} " \
                   f"-e project_id={self.project_id} " \
                   f"-e galloper_url={secrets_tools.unsecret('{{secret.galloper_url}}', project_id=self.project_id)} " \
                   f"-e token=\"{secrets_tools.unsecret('{{secret.auth_token}}', project_id=self.project_id)}\" " \
                   f"getcarrier/control_tower:{constants.CURRENT_RELEASE} " \
                   f"-tid {self.test_uid}"


        if output == "cc":
            channel = self.scan_location
            if channel == "Carrier default config":
                channel = "default"
            #
            execution_json = {
                "job_name": self.name,
                "job_type": job_type,
                "concurrency": concurrency,
                "container": container,
                "execution_params": dumps(parameters),
                "cc_env_vars": cc_env_vars,
                "channel": channel,
            }
            log.info("Resulting CC config: %s", execution_json)
            #
            return execution_json
        return ""