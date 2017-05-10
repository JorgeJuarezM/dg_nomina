# -*- coding:utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError
import uuid


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    STATES = [
        ('01', _('Empleados')),
        ('02', _('Conceptos'))
    ]

    state = fields.Selection(STATES, 'Empleados', default='01')
    payslip_run_id = fields.Many2one('hr.payslip.run', 'Payslip Run Batch')
    payslip_type = fields.Char(
        'Tipo de Nomina', compute="_compute_payslip_type")
    rule_ids = fields.Many2many('hr.salary.rule', string="Rules")

    def _compute_payslip_type(self):
        self.payslip_type = self.payslip_run_id["payslip_type"]

    def execute_type_01(self):
        self.ensure_one()
        self.compute_sheet()

    def execute_type_02(self):
        # retorna opciones para capturar los datos de la estructura salarial
        self.ensure_one()
        self.state = '02'

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }

    def execute_type_02_finish(self):
        self.compute_sheet()

    def compute_sheet(self):
        payslips = self.env['hr.payslip']

        [data] = self.read()

        current_id = self.payslip_run_id.id
        [run_data] = self.env['hr.payslip.run'].browse(current_id).read([
            'date_start',
            'date_end',
            'credit_note',
            'payslip_type',
            'worked_days',
            'name'
        ])

        structure_record = None

        payslip_type = run_data.get('payslip_type')
        worked_days = run_data.get('worked_days')
        payroll_name = run_data.get('name')

        if payslip_type == '02':
            # genera la estructura salarial
            structure_obj = self.env['hr.payroll.structure']
            structure_record = structure_obj.create({
                'code': uuid.uuid4().hex[:6].upper(),
                'name': 'Nomina Extraordinaria',
                'parent_id': None,
                'rule_ids': [(6, 0, self.rule_ids.ids)]
            })

        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')

        if not data['employee_ids']:
            raise UserError(
                _("You must select employee(s) to generate payslip(s)."))

        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            slip_data = self.env['hr.payslip'].onchange_employee_id(
                from_date, to_date, employee.id, contract_id=False)

            struct_id = None
            if bool(structure_record) is False:
                struct_id = slip_data['value'].get('struct_id')
            else:
                struct_id = structure_record.id

            res = {
                'employee_id': employee.id,
                'name': payroll_name,  # slip_data['value'].get('name'),
                'struct_id': struct_id,
                'contract_id': slip_data['value'].get('contract_id'),
                'payslip_run_id': current_id,
                'input_line_ids': [
                    (0, 0, x) for x in
                    slip_data['value'].get('input_line_ids')
                ],
                'worked_days_line_ids': [
                    (0, 0, x) for x in
                    slip_data['value'].get('worked_days_line_ids')
                ],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': run_data.get('credit_note'),
                'worked_days': worked_days
            }
            payslips += self.env['hr.payslip'].create(res)

        payslips.compute_sheet()
        self.env['hr.payslip.run'].browse(current_id).close_payslip_run()
        # close_payslip_run
        return {'type': 'ir.actions.act_window_close'}
