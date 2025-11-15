# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

def post_init(env):
    env['global.calendar.source'].sudo().action_bootstrap_common_sources()

# from odoo import api, SUPERUSER_ID

# def post_init(cr, registry):
#     env = api.Environment(cr, SUPERUSER_ID, {})
#     try:
#         env['global.calendar.source'].sudo().action_bootstrap_common_sources()
#     except Exception:
#         # don't block install
#         pass
