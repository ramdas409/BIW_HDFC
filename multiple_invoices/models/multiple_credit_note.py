from odoo import models, fields, api
import datetime
from odoo.exceptions import ValidationError


class MultipleCreditNote(models.TransientModel):
    _name = 'multiple.credit.note'

    partner_id = fields.Many2one('res.partner', string='Partner', compute='compute_credit_note_wiz')
    invoice_date = fields.Date(string='Credit Date', default=datetime.date.today())
    journal_id = fields.Many2one('account.journal', string='Journal', compute='compute_credit_note_wiz')

    @api.depends('partner_id', 'journal_id')
    def compute_credit_note_wiz(self):
        self.journal_id = self.env['account.journal'].search([('name', '=', 'Tax Invoices')]).id
        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['stock.picking'].browse(selected_ids)
        partner_id_list = []
        for ids in selected_records:
            if ids.credit_note_number:
                raise ValidationError('Selected order(s) is/are Credit note already raised.')
            if not ids.invoiced_id:
                raise ValidationError('Please Select Invoiced Orders')
            if ids.state == 'done' and 'Return of' not in ids.origin: # and (ids.order_status not in ['returned', 'cancelled', 're_dispatched']):
                raise ValidationError('Please Select  Return Orders')
            else:
                if ids.partner_id.parent_id:
                    if ids.partner_id.parent_id.is_company == True:
                        partner_id_list.append(ids.partner_id.parent_id.id)
                    else:
                        partner_id_list.append(ids.partner_id.parent_id.parent_id.id)

        if len(set(partner_id_list)) == 1:
            print(partner_id_list)
            self.partner_id = list(set(partner_id_list))[0]

    def multiple_credit_note(self):
        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['stock.picking'].browse(selected_ids)
        for recs in selected_records:
            tax_type = ''
            if int(recs.partner_id.zip) < 600001 or int(recs.partner_id.zip) > 669999:
                recs.partner_id.update({
                    'property_account_position_id': self.env['account.fiscal.position'].search(
                        [('name', '=', 'Inter State')]).id
                })
                # if there is more than one taxes_id in product.product then below code takes only first,
                # if no taxes_id in product.product then that particular delivery orders invoice will be without any taxes.
                if recs.move_line_ids_without_package.product_id.taxes_id.ids:
                    first_id = recs.move_line_ids_without_package.product_id.taxes_id[0]
                    split_list = first_id.name.split(' ')
                    percentage = [item for item in split_list if '%' in item]
                    num = percentage[0].split('%')[0].strip()
                    tax_type = self.env['account.tax'].search(
                        [('type_tax_use', '=', 'sale'), ('name', 'ilike', 'IGST'), ('name', 'like', str(num))])
                else:
                    tax_type = False
            else:
                # if there is more than one taxes_id in product.product then below code takes only first,
                # if no taxes_id in product.product then that particular delivery orders invoice will be without any taxes.
                if recs.move_line_ids_without_package.product_id.taxes_id.ids:
                    first_id = recs.move_line_ids_without_package.product_id.taxes_id[0]
                    split_list = first_id.name.split(' ')
                    percentage = [item for item in split_list if '%' in item]
                    num = percentage[0].split('%')[0].strip()
                    tax_type = self.env['account.tax'].search(
                        [('type_tax_use', '=', 'sale'), ('name', 'ilike', 'GST'), ('name', 'not like', 'IGST'),
                         ('name', 'like', str(num))])
                else:
                    tax_type = False

            uncompressed = [(0, 0, {
                'customer_ref': recs.unique_ref.unique_ref,
                'delivery_ref': recs.name,
                'product_code': recs.move_ids_without_package.product_id.id,
                'at_status': recs.order_status,
                'compress_product_quantity': recs.move_ids_without_package.product_uom_qty,
                'product_unit_price': recs.move_ids_without_package.product_id.list_price,
                'tax':  False if tax_type == False else tax_type.name,    #here modification
                'total': recs.move_ids_without_package.product_uom_qty * recs.move_ids_without_package.product_id.list_price
            })]

            compressed = [(0, 0, {
                'product_code': recs.move_ids_without_package.product_id.id,
                'compress_product_quantity': recs.move_ids_without_package.product_uom_qty,
                'product_unit_price': recs.move_ids_without_package.product_id.list_price,
                'tax':  False if tax_type == False else tax_type.name,  #here modification
                'total': recs.move_ids_without_package.product_uom_qty * recs.move_ids_without_package.product_id.list_price
            })]

            invoice_lines = [(0, 0, {
                'product_id': recs.move_ids_without_package.product_id.id,
                'quantity': recs.move_ids_without_package.product_uom_qty,
                'product_uom_id': recs.move_ids_without_package.product_uom,
                'tax_ids': False if tax_type == False else tax_type.ids,      #here modification
                # 'price_unit': recs.move_ids_without_package.product_id.list_price,
                # 'price_subtotal': recs.move_ids_without_package.product_uom_qty * recs.move_ids_without_package.product_id.list_price,
            })]

            account_move = self.env['account.move'].create({
                'move_type': 'out_refund',
                'pricelist_id': recs.partner_id.property_product_pricelist,
                'state': 'draft',
                'partner_id': recs.partner_id.id,
                'invoice_date': self.invoice_date,
                'l10n_in_gst_treatment': 'consumer',
                'journal_id': self.journal_id.id,
                'compressed_invoice_change': uncompressed,
                'compressed_invoice': compressed,
                'invoice_line_ids': invoice_lines
            })

            recs.credit_note_number = account_move.id
