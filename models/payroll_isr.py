# -*- coding:utf-8 -*-

from odoo import models, fields, _

TIPO_ISR = [('1', 'Diario'), ('2', 'Semanal'),
            ('3', 'Decenal'), ('4', 'Quincenal'), ('5', 'Mensual')]


class dg_nom_payroll_isr(models.Model):

    _name = 'dg.nom.payroll.isr'
    _description = 'Tablas ISR'

    dg_nom_limite_inferior = fields.Float(_('Límite inferior'), required=True)
    dg_nom_limite_superior = fields.Float(_('Límite superior'), required=True)
    dg_nom_cuota_fija = fields.Float(_('Cuota fija'), required=True)
    dg_nom_excedente = fields.Float(
        _('Porcentaje sobre el excedente del limite inferior'), required=True)
    dg_nom_tipo = fields.Selection(TIPO_ISR, _('Tipo'))
