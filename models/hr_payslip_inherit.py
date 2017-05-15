from odoo import models, fields, api
import logging
import math

_logger = logging.getLogger(__name__)


class BrowsableObject(object):
    def __init__(self, employee_id, dict, env):
        self.employee_id = employee_id
        self.dict = dict
        self.env = env

    def __getattr__(self, attr):
        return attr in self.dict and self.dict.__getitem__(attr) or 0.0


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    worked_days = fields.Float('Dias Laborados', required=True, default=0)

    def calc_sal_gravable(self):
        self.ensure_one()
        return self.calc_SDI() * self.worked_days

    def calc_SDI(self):
        self.ensure_one()

        rule_ids = self.struct_id.rule_ids.ids
        rules = self.env["hr.salary.rule"].search(
            [("id", "in", rule_ids),
             ("is_integrable", "=", True),
             ("rule_type", "=", "PER")])

        calc_salario_base = self.calc_rules(self.id, rules)
        salario_base = calc_salario_base.SUM()

        worked_days = self.worked_days
        salario_diario = salario_base / worked_days

        return salario_diario

    def calc_rules(self, payslip_id, rules):

        class CalcRules(object):
            def __init__(self):
                self.dict = dict()

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

            def SUM(self):
                _sum = 0
                for attr in self.dict:
                    _sum += self.dict.__getitem__(attr) or 0.0
                return _sum

            def addRule(self, rule_name, rule_amount):
                self.dict[rule_name] = rule_amount

        payslip = self.browse(payslip_id)
        categories = BrowsableObject(payslip.employee_id.id, {}, self.env)

        contracts = self.env["hr.contract"].search(
            [("employee_id", "=", payslip.employee_id.id)])

        contract = contracts[0]

        base_dic = {
            "ps": payslip,
            "categories": categories,
            "payslip": payslip
        }

        local_dic = dict(base_dic, contract=contract)
        calc_rules = CalcRules()
        # rule_amount = 0
        for rule in rules:
            amount, qty, rate = rule.compute_rule(local_dic)
            total_amount = amount * qty * rate / 100
            # rule_amount += total_amount
            calc_rules.addRule(rule.code, total_amount)

        return calc_rules

    @api.model
    def calc_imss(self):
        self.ensure_one()
        [data] = self.read()

        GRAND_TOTAL = 0
        SMGVDF = 80.04
        SBC = self.calc_SDI()

        DIAS_LABORADOS = data.get("worked_days", 0)

        # cuota fija
        # (SMGVDF * porcentaje_obrero)*dias_laborados
        [cuota_fija_rec] = self.env.ref("dg_nomina.dg_imss_table_2").read()
        cuota_fija = cuota_fija_rec.get("cuota_obrera", 0)
        cuota_fija = cuota_fija * 10E-3
        cuota_fija += ((1 * SMGVDF) * cuota_fija) * DIAS_LABORADOS
        _logger.info("************************ CUOTA FIJA: %s" % (cuota_fija))
        GRAND_TOTAL += cuota_fija

        # cuota adicional
        # ((SBC - (3 * SMVDF)) * porcentaje_obrero) * DIAS_LABORADOS
        [cuota_adic_rec] = self.env.ref("dg_nomina.dg_imss_table_3").read()
        cuota_adic = cuota_adic_rec.get("cuota_obrera", 0)
        cuota_adic = cuota_adic * 10E-3
        cuota_adic = ((SBC - (SMGVDF * 3)) * cuota_adic) * DIAS_LABORADOS
        cuota_adic = math.ceil(cuota_adic * 100) * 10E-3
        _logger.info("******************* CUOTA ADICIONAL: %s" % (cuota_adic))
        GRAND_TOTAL += 0 if cuota_adic < 0 else cuota_adic

        # Prestaciones en Dinero
        [presta_dinero_rec] = self.env.ref("dg_nomina.dg_imss_table_4").read()
        presta_dinero = presta_dinero_rec.get("cuota_obrera", 0)
        presta_dinero = presta_dinero * 10E-3
        presta_dinero = (SBC * presta_dinero) * DIAS_LABORADOS
        presta_dinero = math.ceil(presta_dinero * 100) * 10E-3
        _logger.info("********************* PREST. DINERO: %s" %
                     (presta_dinero))
        GRAND_TOTAL += presta_dinero

        # Pensionados y Beneficiarios
        [pen_ben_rec] = self.env.ref("dg_nomina.dg_imss_table_5").read()
        pen_ben = pen_ben_rec.get("cuota_obrera", 0)
        pen_ben *= 10E-3
        pen_ben = (SBC * pen_ben) * DIAS_LABORADOS
        pen_ben = math.ceil(pen_ben * 100) * 10E-3
        _logger.info("********************** PEN. y BENEF: %s" % (pen_ben))
        GRAND_TOTAL += pen_ben

        # Invalidez y Vida
        [inv_vida_rec] = self.env.ref("dg_nomina.dg_imss_table_6").read()
        inv_vida = inv_vida_rec.get("cuota_obrera", 0)
        inv_vida *= 10E-3
        inv_vida = (SBC * inv_vida) * DIAS_LABORADOS
        inv_vida = math.ceil(inv_vida * 100) * 10E-3
        _logger.info("*********************** INV. Y VIDA: %s" % (inv_vida))
        GRAND_TOTAL += inv_vida

        # Guarderias y Prestaciones Sociales
        [guarderias_rec] = self.env.ref("dg_nomina.dg_imss_table_9").read()
        guarderias = guarderias_rec.get("cuota_obrera", 0)
        guarderias *= 10E-3
        guarderias = (SBC * guarderias) * DIAS_LABORADOS
        guarderias = math.ceil(guarderias * 100) * 10E-3
        _logger.info("*************** GUARD. Y PREST. SOC: %s" % (guarderias))
        GRAND_TOTAL += guarderias

        # Retiro
        [retiro_rec] = self.env.ref("dg_nomina.dg_imss_table_7").read()
        retiro = retiro_rec.get("cuota_obrera", 0)
        retiro *= 10E-3
        retiro = (SBC * retiro) * DIAS_LABORADOS
        retiro = math.ceil(retiro * 100) * 10E-3
        _logger.info("**************************** RETIRO: %s" % (retiro))
        GRAND_TOTAL += retiro

        # Cesantia y Vejez
        [vejez_rec] = self.env.ref("dg_nomina.dg_imss_table_8").read()
        vejez = vejez_rec.get("cuota_obrera", 0)
        vejez *= 10E-3
        vejez = (SBC * vejez) * DIAS_LABORADOS
        vejez = math.ceil(vejez * 100) * 10E-3
        _logger.info("****************** CESANTIA Y VEJEZ: %s" % (vejez))
        GRAND_TOTAL += vejez

        # VIVIENDA
        [vivienda_rec] = self.env.ref("dg_nomina.dg_imss_table_10").read()
        vivienda = vivienda_rec.get("cuota_obrera", 0)
        vivienda *= 10E-3
        vivienda = (SBC * vivienda) * DIAS_LABORADOS
        vivienda = math.ceil(vivienda * 100) * 10E-3
        _logger.info("************************** VIVIENDA: %s" % (vivienda))
        GRAND_TOTAL += vivienda

        return GRAND_TOTAL

    @api.model
    def calc_isr(self):

        total_gravable = self.calc_sal_gravable()
        periodicidad = 2

        self.env.cr.execute("""
            SELECT * FROM dg_nom_payroll_isr
                where dg_nom_limite_inferior <= %s and
                (dg_nom_limite_superior >= %s or dg_nom_limite_superior = 0)
                and dg_nom_tipo = '%s'
            """, (total_gravable, total_gravable, periodicidad))

        isr_data = self.env.cr.dictfetchone()

        base_gravable = total_gravable - isr_data['dg_nom_limite_inferior']
        porcentaje_excedente = isr_data['dg_nom_excedente']
        cuota_fija = isr_data['dg_nom_cuota_fija']

        return ((base_gravable) * porcentaje_excedente) + cuota_fija

    @api.model
    def get_payslip_lines(self, contract_ids, payslip_id):
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(
                    localdict, category.parent_id, amount)
            if category.code in localdict['categories'].dict:
                amount += localdict['categories'].dict[category.code]
            localdict['categories'].dict[category.code] = amount
            return localdict

        class InputLine(BrowsableObject):
            """a class that will be used into the python code,
            mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(amount) as sum
                    FROM hr_payslip as hp, hr_payslip_input as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()[0] or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours
                    FROM hr_payslip as hp, hr_payslip_worked_days as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code,
            mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute(
                    """SELECT sum(
                                case when hp.credit_note = False
                                    then (pl.total)
                                    else (-pl.total) end)
                            FROM hr_payslip as hp, hr_payslip_line as pl
                            WHERE hp.employee_id = %s AND hp.state = 'done'
                            AND hp.date_from >= %s
                            AND hp.date_to <= %s
                            AND hp.id = pl.slip_id
                            AND pl.code = %s""",
                    (self.employee_id, from_date, to_date, code))
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

        # we keep a dict with the result because a value can be overwritten by
        # another rule with the same code
        result_dict = {}
        rules_dict = {}
        worked_days_dict = {}
        inputs_dict = {}
        blacklist = []
        payslip = self.env['hr.payslip'].browse(payslip_id)
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line

        categories = BrowsableObject(payslip.employee_id.id, {}, self.env)
        inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
        worked_days = WorkedDays(
            payslip.employee_id.id, worked_days_dict, self.env)
        payslips = Payslips(payslip.employee_id.id, payslip, self.env)
        rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)

        baselocaldict = {'categories': categories, 'rules': rules,
                         'payslip': payslips, 'worked_days': worked_days,
                         'inputs': inputs, 'ps': payslip}
        # get the ids of the structures on the contracts and their parent id as
        # well
        contracts = self.env['hr.contract'].browse(contract_ids)
        # structure_ids = contracts.get_all_structures()
        structure_ids = [payslip.struct_id.id]
        # get the rules of the structure and thier children
        rule_ids = self.env['hr.payroll.structure'].browse(
            structure_ids).get_all_rules()
        # run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(
            rule_ids, key=lambda x:x[1])]
        sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)

        for contract in contracts:
            employee = contract.employee_id
            localdict = dict(baselocaldict, employee=employee,
                             contract=contract)
            for rule in sorted_rules:
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                # check if the rule can be applied
                if (rule.satisfy_condition(localdict) and
                        rule.id not in blacklist):
                    # compute the amount of the rule
                    amount, qty, rate = rule.compute_rule(localdict)
                    # check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[
                        rule.code] or 0.0
                    # set/overwrite the amount computed for this rule in the
                    # localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    # sum the amount for its salary category
                    localdict = _sum_salary_rule_category(
                        localdict, rule.category_id,
                        tot_rule - previous_amount)
                    # create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'contract_id': contract.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': contract.employee_id.id,
                        'quantity': qty,
                        'rate': rate,
                        'code_sat': rule.code_sat,
                        'rule_type': rule.rule_type
                    }
                else:
                    # blacklist this rule and its children
                    blacklist += [id for id,
                                  seq in rule._recursive_search_of_rules()]

        return [value for code, value in result_dict.items()]
