# -*- coding: utf-8 -*-
import base64
from odoo import models, fields, api, _

from datetime import date, timedelta
from odoo.exceptions import ValidationError

class SendMailConfig(models.Model):
    _name = 'report.mail.config'
    _description = "Reporting Mail configuration"
    _rec_name = 'subject'

    # user_send = fields.Many2one('res.users', string="From")
    # users_rec = fields.Many2many('res.users', string="To", relation="reports_mail_config_cc")
    # cc = fields.Many2many('res.users', string="CC", relation="reports_mail_config_cc")
    # subject = fields.Text(string="Subject")
    # content = fields.Text(string="Description")
    # report_type = fields.Selection([('data_purge','Data Purge'), ('another', 'Another File')], string="Email Type")
    # customer = fields.Many2one('res.partner', string="Customer")

    user_send = fields.Char(string="From")
    users_rec = fields.Char( string="To")
    cc = fields.Char(string="CC")
    subject = fields.Text(string="Subject")
    content = fields.Text(string="Description")
    report_type = fields.Selection([('data_purge', 'Data Purge'), ('another', 'Another File')], string="Email Type")

    @api.constrains('report_type')
    def _check_unique_my_field(self):
        duplicates = self.search([('report_type', '=', self.report_type)])
        if len(duplicates) > 1:
            raise ValidationError("Report must be unique for every record")


