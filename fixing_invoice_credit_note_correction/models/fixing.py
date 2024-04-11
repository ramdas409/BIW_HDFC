# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError

class StockPickingFixing(models.Model):
    _inherit = 'stock.picking'

    def map_fixing_invoice_credit_note(self):
        selected_ids = self.env.context.get('active_ids', [])
        data = self.env['stock.picking'].browse(selected_ids)
        for rec in data:
            if('Return of ' not in rec.origin):
                updating_value = self.env['stock.picking'].search([('origin','=','Return of '+rec.name)],limit=1)
                rec.return_order = updating_value.id
                res={'invoiced_id':rec.invoiced_id.id,'invoice_date':rec.invoice_date,'credit_note_number':rec.credit_note_number.id,'credit_note_date':rec.credit_note_date}
                updating_value.update(res)
            else:
                raise ValidationError("please select Source document orders that doesn't contain  \'Return of\'")


    def map_fixing_invoice_from_return_dashboard(self):
        selected_ids = self.env.context.get('active_ids', [])
        data = self.env['stock.picking'].browse(selected_ids)
        for rec in data:
            if ('Return of ' in rec.origin):
                vals=rec.origin.split('Return of')[1].strip()
                searched_data=self.env['stock.picking'].search([('name','=',vals)],limit=1)
                res={'invoiced_id':searched_data.invoiced_id.id,'invoice_date':searched_data.invoice_date,'credit_note_number':searched_data.credit_note_number.id,'credit_note_date':searched_data.credit_note_date}
                rec.update(res)
                searched_data.return_order=rec.id




