# -*- coding:utf-8 -*-
from odoo import models, fields, _


RULE_TYPES = [
    ('PER', _('Percepción')),
    ('DED', _('Deducción'))
]


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    rule_type = fields.Selection(RULE_TYPES, _('Tipo de Concepto'),
                                 required=True)
    code_sat = fields.Char(_('Código SAT'), required=True)
    is_integrable = fields.Boolean(_('Es Integrable'), required=True)
