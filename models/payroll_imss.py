# -*- encoding: utf-8 -*-

from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class PayrollImss(models.Model):

    _name = 'dg.nom.payroll.imss'
    _description = 'Tabla de Cuotas Obreras IMSS'
    _rec_name = 'concepto'

    concepto = fields.Char('Concepto', required=True)
    cuota_patronal = fields.Float('Cuota patronal', required=True)
    cuota_obrera = fields.Float('Cuota obrera', required=True)
    total = fields.Float('Total', required=True)
    base_salarial = fields.Char('Base salarial', required=True)
