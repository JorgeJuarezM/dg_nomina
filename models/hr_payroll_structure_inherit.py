from odoo import models, fields, _


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    active = fields.Boolean(_("Activo"), default=True)
