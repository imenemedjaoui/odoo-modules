from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    _inherit = "project.task"

    # Champs de chronomètre
    timer_running = fields.Boolean(
        string="Chronomètre en marche",
        default=False,
        help="Indique si le chronomètre est actuellement en marche."
    )
    timer_paused = fields.Boolean(
        string="Chronomètre en pause",
        default=False,
        help="Indique si le chronomètre est en pause."
    )
    timer_start_datetime = fields.Datetime(
        string="Date/heure de démarrage",
        readonly=True,
        help="Dernière date et heure auxquelles le chronomètre a démarré."
    )
    pause_start_datetime = fields.Datetime(
        string="Date/heure de mise en pause",
        readonly=True,
        help="Date et heure auxquelles la pause a commencé."
    )
    first_start_datetime = fields.Datetime(
        string="Première date de démarrage",
        readonly=True,
        help="Date et heure du tout premier lancement du chronomètre."
    )
    allocated_reached_datetime = fields.Datetime(
        string="Date de dépassement des heures allouées",
        readonly=True,
        help="Date et heure auxquelles les heures allouées ont été atteintes."
    )
    timer_spent_total = fields.Float(
        string="Temps passé accumulé (heures)",
        default=0.0,
        help="Temps total passé (en heures) accumulé par le chronomètre depuis le dernier enregistrement en feuille de temps."
    )
    timer_pause_total = fields.Float(
        string="Temps total en pause (heures)",
        default=0.0,
        help="Somme du temps passé en pause pour cette tâche depuis le dernier réinitialisation du chronomètre."
    )
    timer_display = fields.Char(
        string="Chronomètre",
        compute="_compute_timer_display",
        store=False
    )
    timer_color = fields.Char(
        string="Couleur du chronomètre",
        compute="_compute_timer_display",
        store=False,
        help="Couleur à utiliser pour l'affichage du chronomètre selon l'état."
    )
    limit_reached = fields.Boolean(
        string="Limite atteinte",
        compute="_compute_timer_display",
        store=False,
        help="Indique si les heures allouées ont été atteintes pendant l'exécution du chronomètre."
    )
    # remaining_hours = fields.Float(
    #     compute="_compute_remaining_hours_new",
    #         store=False,   # ou True si tu veux stocker, à toi de voir
    # groups=False,  # <-- TRÈS IMPORTANT : enlève les groupes hérités
    # readonly=True, # optionnel, mais logique pour un compute
    # )

    @api.depends('timer_running', 'timer_paused', 'timer_start_datetime', 'timer_spent_total', 'timer_pause_total')
    def _compute_timer_display(self):
        """
        Calcule une chaîne formatée (HH:MM:SS) représentant le temps passé. La couleur change selon l'état : vert si en marche,
        rouge si en pause et noir si jamais démarré.
        """
        for task in self:
            # calcul du temps écoulé en secondes
            if task.timer_running and task.timer_start_datetime:
                now = fields.Datetime.now()
                delta = now - task.timer_start_datetime
                elapsed_seconds = task.timer_spent_total * 3600.0 + delta.total_seconds()
                
                # Vérifier si on a atteint les heures allouées
                if task.allocated_hours:
                    current_hours = elapsed_seconds / 3600.0
                    timesheet_hours = sum(task.timesheet_ids.mapped('unit_amount'))
                    total_hours = timesheet_hours + current_hours
                    
                    if total_hours >= task.allocated_hours and not task.allocated_reached_datetime:
                        # Mettre en pause automatiquement
                        task._pause_timer()
                        task.allocated_reached_datetime = now
            else:
                elapsed_seconds = task.timer_spent_total * 3600.0
            hours = int(elapsed_seconds // 3600)
            minutes = int((elapsed_seconds % 3600) // 60)
            seconds = int(elapsed_seconds % 60)
            task.timer_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # Définir si la limite est atteinte
            task.limit_reached = bool(task.allocated_reached_datetime)
            
            # définir la couleur selon l'état
            if not task.timer_start_datetime:
                task.timer_color = 'black'
            elif task.timer_running and not task.timer_paused:
                task.timer_color = 'green'
            elif task.timer_paused:
                task.timer_color = 'red'
            else:
                task.timer_color = 'black'

    @api.depends('allocated_hours', 'timesheet_ids.unit_amount', 'timer_spent_total')
    def _compute_remaining_hours_new(self):
        """
        Calcule les heures restantes en tenant compte des heures allouées, des feuilles de temps existantes et du temps accumulé mais non enregistré.
        """
        for task in self:
            allocated = task.allocated_hours or 0.0
            timesheet_hours = sum(task.timesheet_ids.mapped('unit_amount'))
            current_spent = task.timer_spent_total
            # BUBBLE FIX START
            # task.remaining_hours = max(0.0, allocated - (timesheet_hours + current_spent))


    # Bouton pour démarrer/pauser/reprendre
    def action_timer_toggle(self):
        """
        Lance ou met en pause le chronomètre. Si le chronomètre est arrêté, on le lance ;
        s'il est en marche, on le met en pause ; s'il est en pause, on le reprend.
        """
        for task in self:
            if not task.timer_running and not task.timer_paused:
                task._start_timer()
            elif task.timer_running and not task.timer_paused:
                task._pause_timer()
            elif task.timer_paused:
                task._resume_timer()
        return True

    def action_timer_stop(self):
        """
        Arrête le chronomètre et ouvre l'assistant de création de feuille de temps. Le temps accumulé est passé à l'assistant.
        """
        for task in self:
            # Si en marche, mettre en pause pour accumuler la durée courante
            if task.timer_running and not task.timer_paused:
                task._pause_timer()
            if task.timer_spent_total <= 0:
                raise UserError(_('Aucune durée à enregistrer. Lancez le chronomètre avant de l\'arrêter.'))
            return task._open_timesheet_wizard(task.timer_spent_total)
        return True


    # Méthodes internes de gestion du chronomètre
    def _start_timer(self):
        now = fields.Datetime.now()
        for task in self:
            task.timer_running = True
            task.timer_paused = False
            task.timer_start_datetime = now
            # mémoriser la première date de démarrage
            if not task.first_start_datetime:
                task.first_start_datetime = now
            # ⚠️ NE PLUS TOUCHER À allocated_reached_datetime ICI
        return True



    def _pause_timer(self):
        now = fields.Datetime.now()
        for task in self:
            if not task.timer_running or task.timer_paused:
                continue
            # additionner la durée écoulée
            if task.timer_start_datetime:
                delta = now - task.timer_start_datetime
                task.timer_spent_total += delta.total_seconds() / 3600.0
            task.timer_running = False
            task.timer_paused = True
            task.pause_start_datetime = now
            # ⚠️ NE PLUS TOUCHER À allocated_reached_datetime ICI NON PLUS
        return True


    def _resume_timer(self):
        now = fields.Datetime.now()
        for task in self:
            if not task.timer_paused:
                continue
            # comptabiliser la durée de pause
            if task.pause_start_datetime:
                delta_pause = now - task.pause_start_datetime
                task.timer_pause_total += delta_pause.total_seconds() / 3600.0
            task.timer_running = True
            task.timer_paused = False
            task.timer_start_datetime = now
        return True

    def _reset_timer(self):
        for task in self:
            task.timer_running = False
            task.timer_paused = False
            task.timer_start_datetime = False
            task.pause_start_datetime = False
            task.timer_spent_total = 0.0
            task.timer_pause_total = 0.0
            task.allocated_reached_datetime = False
        return True

    def _open_timesheet_wizard(self, time_spent):
        self.ensure_one()
        context = {
            'default_task_id': self.id,
            # 'default_name': self.name,
            'default_name': '',
            'default_time_spent': time_spent,
        }
        return {
            'name': _('Nouvelle feuille de temps'),
            'view_mode': 'form',
            'res_model': 'project.task.timer.wizard',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }

    @api.model
    def get_timer_info(self, task_id):
        """
        Méthode RPC pour le widget Javascript : renvoie l'affichage, la couleur et le temps restant.
        """
        task = self.browse(task_id)
        if not task:
            return {}

        # État AVANT recalcul
        had_limit = bool(task.allocated_reached_datetime)

        # Recalcule l’affichage + logique de limite
        task._compute_timer_display()

        # État APRÈS recalcul
        has_limit = bool(task.allocated_reached_datetime)

        # True UNIQUEMENT au moment où on franchit la limite
        just_reached = has_limit and not had_limit

        return {
            'display': task.timer_display,
            'color': task.timer_color,
            'remaining_hours': task.remaining_hours,
            # "a atteint la limite (déjà ou maintenant)"
            'allocated_limit_reached': has_limit,
            # "vient tout juste d’atteindre la limite"
            'limit_reached': just_reached,
        }

