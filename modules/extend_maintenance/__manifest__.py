{
    'name': 'Custom Maintenance Equipment',
    'version': '17.0.1.0.0',
    'summary': 'Ajoute des champs personnalisés aux équipements de maintenance',
    'description': 'Module permettant d’ajouter des champs supplémentaires aux équipements de maintenance sans modifier le module natif.',
    'author': 'Imène M',
    'category': 'Maintenance',
    'depends': ['maintenance', 'stock', 'maintenance_product', 'purchase', 'mail'],
    'data': [
        'views/maintenance_equipment_view.xml',
        'views/maintenance_request_views.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
