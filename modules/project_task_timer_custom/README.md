# 📦 Module: Project Task Timer Custom  

## 📘 Overview  
This module adds a **real-time task timer** inside Odoo 17 Project.  
Users can start, pause, resume, and stop the timer directly from the **task Form view**.  
In the **List** and **Kanban** views, the timer is displayed in read-only mode so users can monitor the elapsed time at a glance.  
A wizard automatically appears when stopping the timer to help create a corresponding **timesheet entry**.  
The module also tracks available allocated hours and triggers the wizard automatically when the limit is reached.

---

## ✨ Features  
- Real-time timer embedded inside project tasks (with controls in the Form view)  
- Read-only timer display in List and Kanban task views  
- Start / Pause / Resume / Stop buttons on the Form view  
- Timer color indicators depending on state (running, paused, never started)  
- Automatic wizard to create a new timesheet line when the timer stops  
- Wizard also auto-opens if allocated hours reach their limit  
- Fields that record the real start time, stop time, and remaining hours  
- Custom JS widget + XML templates for dynamic rendering

---

## 🧩 Technical Details  

### Models Modified  
- `project.task`  
  - Adds fields for timer management (start datetime, stop datetime, allocated hours, remaining hours…)  
  - Adds methods related to timer behavior (start/pause/stop logic)

### New Models  
- `task.timer.wizard`  
  - Wizard triggered upon timer stop  
  - Creates a corresponding timesheet line linked to the task

### Views Added  
- `project_task_views.xml`  
- `task_timer_wizard_views.xml`  
- `task_timer.xml` (QWeb template for timer widget)

### Security  
- `ir.model.access.csv`  
  - Access rights for the wizard model  
- No custom record rules  

---

## ⚙️ Installation  
1. Copy the module into your Odoo `addons` directory  
2. Update Odoo app list  
3. Install the module from Apps

---

## 🔧 Compatibility  
- **Odoo Version:** 17 Community  
- Python 3.10+  

---

## 🙋‍♀️ Author  
**Imène Medjaoui**

---

## 📜 License  
LGPL-3.0
