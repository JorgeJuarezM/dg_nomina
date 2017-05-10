# -*- coding:utf-8 -*-

{
    'name': 'Cálculo y Timbrado de Nómina 1.2.1',
    'version': '1.2.2',
    'category': 'Desiteg',
    'description': '@jorgejuarezmx',
    'author': 'Desiteg - Desarrolladora de Sistemas \
    Tecnológicos de Guerrero SA de CV',
    'website': 'http://www.desiteg.com',
    'depends': [
        'hr_payroll'
    ],
    'data': [
        'views/hr_payroll_views_inherit.xml',
        'data/delete_hr_salary_rule_category_data.xml'
    ],
    'active': False,
    'installable': True,
    'auto_install': False,
}
