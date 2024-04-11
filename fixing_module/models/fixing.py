# -*- coding: utf-8 -*-
from odoo import api, models, fields, _

class StockPickingFixing(models.Model):
    _inherit = 'stock.picking'
    
    # First time -------------------------------------------
    #def courier_id_to_char(self):
    #   for recs in self:
    #      if recs.courier_company.id:
    #         recs.courier_company_id = recs.courier_company.courier_company
    #         recs.hub = recs.courier_company.hub
    #         recs.airport = recs.courier_company.airport
               
               
    # Second time ------------------------------------------
    def courier_id_to_char(self):
        for recs in self:
            if recs.courier_company_id.id and recs.hub == False and recs.airport == False:
                # recs.courier_company_id = recs.courier_company.courier_company
                pin_code_id = self.env['courier.company.code'].search([('pin_code', '=', recs.zip), ('courier_company', '=', recs.courier_company_id.id)])
                recs.hub = pin_code_id.hub
                recs.airport = pin_code_id.airport
