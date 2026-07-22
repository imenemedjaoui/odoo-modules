{
    "name": "Project Task Timer Custom",
    "version": "17.0.1.2.0",
    "summary": "Chronomètre en temps réel pour les tâches de projet",
    "description": """
        Ce module ajoute un chronomètre en temps réel aux tâches de projet dans Odoo 17.\n
        Les utilisateurs disposent de boutons pour démarrer, mettre en pause et arrêter le chronomètre directement depuis les vues Formulaire, Liste et Kanban des tâches.\n
        Le chronomètre change de couleur en fonction de son état : vert lorsqu’il est en marche, rouge lorsqu’il est en pause et noir tant qu’il n’a jamais été lancé.\n
        Deux champs datetime permettent d’enregistrer la date et l’heure du premier lancement du chronomètre ainsi que la date à laquelle la limite d’heures allouées est atteinte.\n
        À l’arrêt du chronomètre, un assistant « Nouvelle feuille de temps » s’ouvre automatiquement afin de créer une ligne de feuille de temps liée à la tâche.\n
        L’assistant pré‑remplit le nom de la ligne avec celui de la tâche et soustrait automatiquement le temps passé des heures allouées. Un champ « Temps restant » sur la tâche affiche les heures disponibles.\n
        Si la limite d’heures allouées est atteinte sans arrêt manuel, l’assistant s’ouvre également de manière automatique.\n
    """,
    "author": "Imène M",
    "website": "",
    "license": "LGPL-3",
    "category": "Project",
    "depends": ["base", "analytic", "project", "hr_timesheet"],
    "data": [
        "security/ir.model.access.csv",
        "views/project_task_views.xml",
        "views/task_timer_wizard_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "project_task_timer_custom/static/src/js/task_timer.js",
            "project_task_timer_custom/static/src/js/timer_display_widget.js",
            "project_task_timer_custom/static/src/xml/task_timer.xml",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}