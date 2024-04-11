# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError

class AirwayBillInherit(models.Model):
    _inherit = 'air.way.bill'

    def map_fixing_delievry_orders_for_awb(self):


        for rec in self:
            if rec.delivery_order_number:
                rec.delivery_order_number_many=[(4, rec.delivery_order_number.id)]



    # def map_fixing_invoice_from_return_dashboard(self):
    #     selected_ids = self.env.context.get('active_ids', [])
    #     data = self.env['stock.picking'].browse(selected_ids)
    #     for rec in data:
    #         if ('Return of ' in rec.origin):
    #             updating_value = self.env['stock.picking'].search([('name', '=', 'Return of ' + rec.name)], limit=1)
    #             rec.return_order = updating_value.id
    #             print('44444444444444444444444', rec.return_order)
    #             res = {'invoiced_id': rec.invoiced_id.id, 'invoice_date': rec.invoice_date,
    #                    'credit_note_number': rec.credit_note_number, 'credit_note_date': rec.credit_note_date}
    #             print(55555555555555555555, res)
    #             updating_value.update(res)
    #         else:
    #             raise ValidationError("please select Source document orders that doesn't contain  \'Return of\'")
    #

