# 📦 Module: Global Calendar

## 📘 Overview

This module provides a unified **global calendar** that automatically
aggregates dates from multiple configured models.\
Each user can define their own sources, allowing the system to collect
date fields from any Odoo model and centralize them into a single
calendar view.\
It is designed to improve visibility across tasks, deadlines, and events
coming from multiple modules.

------------------------------------------------------------------------

## ✨ Features

-   Centralized calendar aggregating dates from multiple models\
-   Per-user configuration of calendar data sources\
-   Automatic creation and update of calendar events via cron jobs\
-   Color-coded events based on source configuration\
-   Custom popover template disabling quick-edit on calendar items

------------------------------------------------------------------------

## 🧩 Technical Details

### Models Modified

-   *None*

### New Models

-   `global.calendar.source`
    -   Stores user-specific model mappings: model name, date field,
        color settings\
-   `global.calendar.event`
    -   Stores computed calendar events aggregated from configured
        sources

### Views Added

-   `global_calendar_event_views.xml`\
-   `global_calendar_source_views.xml`\
-   Custom calendar popover override: `calendar_popover_no_edit.xml`

### Security

-   ACL rules (`ir.model.access.csv`)\
-   Additional record rules (`security.xml`)

------------------------------------------------------------------------

## ⚙️ Installation

1.  Copy module into your Odoo `addons` directory\
2.  Update Odoo app list\
3.  Install the module from Apps

------------------------------------------------------------------------

## 🔧 Compatibility

-   **Odoo Version:** 17 Community\
-   Python 3.10+

------------------------------------------------------------------------

## 🙋‍♀️ Author

**Imène Medjaoui**

------------------------------------------------------------------------

## 📜 License

LGPL-3.0
