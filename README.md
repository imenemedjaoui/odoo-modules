# <img src="assets/odoo.png" height="60"/> Odoo Custom Modules  
A curated collection of my custom Odoo 17 Community modules.  
This repository centralizes all my developments: feature extensions, business logic, workflow automations, system integrations, and customizations crafted for real-world projects.

---

## 🚀 About This Repository  
This repo contains:  
- Custom Odoo 17 Community modules  
- Clean, structured, maintainable code  
- Real business use-cases  
- Integrations (Nextcloud, ONLYOFFICE, external services, etc.)  
- Automation & workflow enhancements  

Each module lives in its own directory inside `/modules/` and includes:  
- A manifest  
- Models  
- Views  
- Security rules  
- Data files  
- A dedicated README  
- Optional assets

---

## 📁 Repository Structure

```
odoo-modules/
│
├── README.md                 
│
├── modules/                  
│   ├── module_1/             
│   │   ├── __init__.py
│   │   ├── __manifest__.py
│   │   ├── models/
│   │   ├── views/
│   │   ├── i18n/
│   │   ├── security/
│   │   ├── data/
│   │   ├── static/
│   │   └── README.md         
│   │
│   ├── module_2/
│   ├── module_3/
│   └── ...
│
└── assets/
```

---

## 📦 Modules List  

```
- [ ] module_name_1  
- [ ] module_name_2  
- [ ] module_name_3  
- [ ] ...
```

---

## 🧰 Requirements  
- **Odoo 17 Community**  
- Python 3.10+  
- PostgreSQL  
- Dependencies specific to each module (see individual READMEs)

---

## ⚙️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/imenemedjaoui/odoo-modules.git
   ```

2. Add the `/modules/` directory to your Odoo `addons_path`:
   ```text
   addons_path = /path/to/odoo/addons,/path/to/repo/odoo-modules/modules
   ```

3. Restart Odoo:
   ```bash
   sudo systemctl restart odoo
   ```

4. Update the app list in Odoo and install the module you want.

---

## 🔄 Updating Modules
```bash
git pull
sudo systemctl restart odoo
```

---

## 🤝 Contribution  
This repository is personal, but feel free to fork it, open issues, or suggest improvements.

---

## 👩‍💻 Author  
**Imène Medjaoui**

---

## 📜 License  
LGPL-3.0
