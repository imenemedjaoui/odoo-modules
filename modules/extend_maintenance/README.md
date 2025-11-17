# 📦 Module: Custom Maintenance Equipment

## 📘 Overview

This module extends the standard Odoo maintenance application by adding
custom fields, workflow enhancements, and improvements to equipment
tracking and maintenance request processing.\
It enriches both **maintenance.equipment** and **maintenance.request**
models to support calibration, recall management, execution mode
tracking, purchasing links, and more.

------------------------------------------------------------------------

## ✨ Features

-   Adds new equipment status field (`state_custom`) with multiple
    operational states\
-   Adds calibration and recall dates on maintenance equipment\
-   Adds a new execution mode (`internal` / `external`) on maintenance
    requests\
-   Adds enhanced workflow logic including subcontracting support\
-   Integrates maintenance requests with purchase orders\
-   Extends views for equipment and maintenance requests with custom
    fields

------------------------------------------------------------------------

## 🧩 Technical Details

### Models Modified

-   `maintenance.equipment`
    -   New fields: `state_custom`, `calibration_date`, `recall_date`\
    -   Additional logic for stock and cost computations (extended code
        in file)
-   `maintenance.request`
    -   New field `maintenance_flow` (execution mode)\
    -   New behaviors for purchasing, validation, and subcontracted flow
        management

### New Models

-   *None*

### Views Added

-   `maintenance_equipment_view.xml`\
-   `maintenance_request_views.xml`

### Security

-   No extra ACLs\
-   No custom record rules

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
