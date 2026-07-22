from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectTaskTimerWizard(models.TransientModel):
    _name = 'project.task.timer.wizard'
    _description = 'Assistant de création de feuille de temps pour le chronomètre de tâche'

    task_id = fields.Many2one('project.task', string='Tâche', required=True)
    name = fields.Char(string='Description', required=True)
    time_spent = fields.Float(string='Durée à enregistrer (heures)', required=True, digits=(16, 2))
    time_spent_display = fields.Char(string='Durée', compute='_compute_time_spent_display', store=False)

    @api.depends('time_spent')
    def _compute_time_spent_display(self):
        """Convertit le temps en heures décimales en format HH:MM avec arrondi des secondes"""
        for wizard in self:
            if wizard.time_spent:
                total_minutes = wizard.time_spent * 60
                # Arrondir les minutes (si >= 0.75 min = 45 sec, on arrondit à la minute supérieure)
                total_minutes = round(total_minutes)
                hours = int(total_minutes // 60)
                minutes = int(total_minutes % 60)
                wizard.time_spent_display = f"{hours}:{minutes:02d}"
            else:
                wizard.time_spent_display = "0:00"

    def action_confirm(self):
        """
        Crée une ligne de feuille de temps à partir des informations fournies et réinitialise le chronomètre.
        """
        self.ensure_one()
        if self.time_spent <= 0:
            raise UserError(_('La durée à enregistrer doit être positive.'))
        task = self.task_id
        # Déterminer l'employé courant
        employee = self.env.user.employee_id
        if not employee:
            raise UserError(_('Aucun employé associé à l’utilisateur courant.'))
        # Créer la ligne de feuille de temps
        values = {
            'name': self.name,
            'project_id': task.project_id.id or False,
            'task_id': task.id,
            'employee_id': employee.id,
            'unit_amount': self.time_spent,
            'date': fields.Date.today(),
        }
        analytic_line = self.env['account.analytic.line'].create(values)
        # Soustraire la durée enregistrée du champ allocated_hours (heures allouées)
        # if task.allocated_hours:
        #     task.allocated_hours -= self.time_spent
        #     if task.allocated_hours < 0:
        #         task.allocated_hours = 0
        # Réinitialiser le chronomètre
        task._reset_timer()
        return {'type': 'ir.actions.act_window_close'}