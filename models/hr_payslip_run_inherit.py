# -*- coding:utf-8 -*-

from odoo import api, models, fields, _


class HrPayslipRun(models.Model):
    _name = "hr.payslip.run"
    _inherit = ["hr.payslip.run", "mail.thread"]

    PAY_SLIP_TYPES = [
        ('01', _('Ordinaria')),
        ('02', _('Extraordinaria'))
    ]

    worked_days = fields.Float(_("Dias laborados"),
                               readonly=True,
                               states={'draft': [('readonly', False)]})

    payslip_type = fields.Selection(PAY_SLIP_TYPES, _('Tipo de Nomina'),
                                    readonly=True,
                                    required=True,
                                    states={'draft': [('readonly', False)]})

    state = fields.Selection([
        ('draft', 'Draft'),
        ('ready', 'Generated'),
        ('done', 'Confirmed'),
        ('close', 'Close'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')

    @api.multi
    def close_payslip_run(self):
        return self.write({'state': 'ready'})

    @api.onchange('date_start', 'date_end')
    def on_change_date_start_end(self):

        days = 0
        try:
            date_end = fields.Date.from_string(self.date_end)
            date_start = fields.Date.from_string(self.date_start)

            days = (date_end - date_start).days + 1
        except Exception:
            pass

        return {
            "value": {
                "worked_days": days
            }
        }

    def action_hr_payslip_by_employees(self):

        partial_id = self.env["hr.payslip.employees"].create({
            'payslip_run_id': self.id
        })

        return {
            'name': _("Payslip Process"),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'hr.payslip.employees',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'res_id': partial_id.id
        }

    def action_hr_payslip_done(self):
        # action_payslip_done
        self.ensure_one()
        for slip in self.slip_ids:
            slip.action_payslip_done()
        self.write({'state': 'done'})

    def action_hr_payslip_close(self):
        self.write({'state': 'close'})
