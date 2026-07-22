from odoo import http
from odoo.http import request


class ProjectTaskTimerController(http.Controller):

    @http.route('/project_task_timer/get_timer_info', type='json', auth='user')
    def get_timer_info(self, task_id):
        """
        Endpoint JSON pour récupérer les informations du chronomètre d'une tâche.
        """
        task = request.env['project.task'].browse(task_id)
        if not task.exists():
            return {
                'display': '00:00:00',
                'color': 'black',
                'remaining_hours': 0.0,
                'allocated_limit_reached': False,
            }
        
        return task.get_timer_info(task_id)