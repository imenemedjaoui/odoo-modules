# 📦 Module: Force Mail SMTP

## 📘 Overview

This module forces Odoo to always use a specific SMTP server and
disables the automatic deletion of sent emails.\
It ensures consistent delivery behavior by overriding default
email-sending logic.

------------------------------------------------------------------------

## ✨ Features

-   Forces all outgoing emails to use the first configured SMTP server\
-   Prevents automatic deletion of sent emails (`auto_delete = False`)\
-   Reapplies SMTP and deletion rules even when email records are edited

------------------------------------------------------------------------

## 🧩 Technical Details

### Models Modified

-   `mail.mail`
    -   Overrides `create()` to force SMTP server and disable
        auto-deletion\
    -   Overrides `write()` to reapply the same constraints

### New Models

-   *None*

### Views Added

-   *None*

### Security

-   No custom ACL rules\
-   No record rules

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
