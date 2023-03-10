from pylon.core.tools import web, log

from tools import auth
from tools import theme


class Slot:  # pylint: disable=E1101,R0903
    """
        Slot Resource

        self is pointing to current Module instance

        web.slot decorator takes one argument: slot name
        Note: web.slot decorator must be the last decorator (at top)

        Slot resources use check_slot auth decorator
        auth.decorators.check_slot takes the following arguments:
        - permissions
        - scope_id=1
        - access_denied_reply=None -> can be set to content to return in case of 'access denied'

    """

    @web.slot('security_sast_content')
    @auth.decorators.check_slot(
        [],
        access_denied_reply=theme.access_denied_part
    )
    def content(self, context, slot, payload):
        log.info('slot: [%s] || payload: [%s]', slot, payload)
        with context.app.app_context():
            return self.descriptor.render_template(
                'app/content.html',
            )

    @web.slot('security_sast_scripts')
    def scripts(self, context, slot, payload):
        log.info('slot: [%s] || payload: [%s]', slot, payload)
        with context.app.app_context():
            return self.descriptor.render_template(
                'app/scripts.html',
            )

    @web.slot('security_sast_styles')
    def styles(self, context, slot, payload):
        log.info('slot: [%s] || payload: [%s]', slot, payload)
        with context.app.app_context():
            return self.descriptor.render_template(
                'app/styles.html',
            )
