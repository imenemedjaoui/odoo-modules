# -*- coding: utf-8 -*-
{
    "name": "Global Calendar",
    "summary": "Global Calendar: aggregates all dates from multiple configured models. (by user)",
    "version": "17.0.1.2.0",
    "category": "Productivity",
    "author": "Imène M",
    "license": "LGPL-3",
    "depends": ["base", "web"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/global_calendar_event_views.xml",
        "views/global_calendar_source_views.xml",
        "data/cron.xml",
        "data/actions.xml"
    ],

    "assets": {
        "web.assets_backend": [
            "global_calendar/static/src/xml/calendar_popover_no_edit.xml",
        ],
    },


    "icon": "/global_calendar/static/description/icon.png",
    "application": True,
    "post_init_hook": "post_init",
}
