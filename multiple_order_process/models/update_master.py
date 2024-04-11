# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime


class UpdateOrders(models.Model):
    _name = 'update.rec'

    awb_nos = fields.Char(string='AWB NO')
    pod_date = fields.Date(string='DELIVERED ON')
    person_delv = fields.Char(string='PERSON DELIVERED')
    return_date = fields.Date(string='RETURNED ON')
    return_reason = fields.Char(string='RETURN REASON')
    cancel_order = fields.Char(string='ORDER NUMBER')
    cancel_date = fields.Date(string='CANCELED ON')
    cancel_reason = fields.Char(string='CANCEL REASON')
    name = fields.Char(string='NAME')
    add1 = fields.Char(string='ADD1')
    add2 = fields.Char(string='ADD2')
    city = fields.Char(string='CITY')
    pin = fields.Char(string='PINCODE')
    phone = fields.Char(string='PHONE')
    email = fields.Char(string='EMAIL')
    unique_ref= fields.Char(string="Biw Unique reference")

class UpdateMasterWizard(models.TransientModel):
    _name = 'update.master.wizard'

    # courier1 = fields.Many2one('res.partner', string='Courier', domain="[('is_company','=', True), ('courier_details','=', True)]")
    to_update = fields.Selection([('delivery', 'Delivered'), ('return', 'Returned'), ('cancelled', 'Cancelled'),
                                  ('returned_n_reshipped', 'Re-Dispatch')], required=True, string='To Update as')

    def update_master_action_submit(self):
        # selected ids in list
        selected_ids = self.env.context.get('active_ids', [])

        # converting selected ids to record tuple
        selected_records = self.env['update.rec'].browse(selected_ids)

        awb_no = [rlist.unique_ref for rlist in self.env['pemt.rec'].search([]) if rlist.unique_ref]
        #order_no = [rlist.ref_no.strip() for rlist in self.env['pemt.rec'].search([]) if rlist.ref_no]
        company_ids = []
        # company_ids = [rlist.customer_name.parent_id for rlist in self.env['pemt.rec'].search([]) if rlist.customer_name.parent_id]
        vals = []
        delete = []
        created_retry_line = []

        for lines in selected_records:
            if lines.unique_ref:
                unique_ref_searched = self.env['pemt.rec'].search([('unique_ref', '=', lines.unique_ref.strip())],order='create_date desc',limit=1)
            # if lines.cancel_order:
            #     order_no_searched = self.env['pemt.rec'].search([('ref_no', '=', lines.cancel_order.strip())])

            if self.to_update == 'delivery':
                if lines.unique_ref.strip():
                    if lines.unique_ref.strip() in awb_no:
                        # if lines.awb_nos == awb_no_searched.awb_nos:
                        if unique_ref_searched.order_status == 'dispatched':
                            if lines.pod_date and lines.pod_date and unique_ref_searched.dispatched_on:
                                unique_ref_searched.update({
                                    'pod_date': lines.pod_date,
                                    'person_delv': lines.person_delv,
                                    'up_pod_date': datetime.date.today()
                                })
                                unique_ref_searched.delivery_id.order_status = 'delivered'
                                delete.append(lines.id)
                                # lines.unlink()
                            else:
                                raise UserError("date should be greater than Dispatched date")
                        else:
                            raise UserError('Order must be "Dispatched" to set the order as "Delivered"')
                    else:
                        raise UserError("BIW Unique Reference Number Doesn't exist")
                else:
                    raise UserError("Empty BIW Unique Reference Number")

            if self.to_update == 'return':
                if lines.unique_ref:
                    if lines.unique_ref.strip() in awb_no:
                        return_list = []
                        if unique_ref_searched.order_status == 'dispatched' or unique_ref_searched.order_status == 'delivered':
                            if unique_ref_searched.order_status == 'dispatched':
                                if lines.return_date and lines.return_date and unique_ref_searched.dispatched_on:
                                    return_list.append(True)
                                else:
                                    return_list.append(False)
                                    raise UserError("Date should be greater than dispatched date")
                            if unique_ref_searched.order_status == 'delivered':
                                if lines.return_date and lines.return_date > unique_ref_searched.up_pod_date:
                                    return_list.append(True)
                                else:
                                    return_list.append(False)
                                    raise UserError("Date should be greater than Delivered Date")
                        else:
                            raise UserError(
                                'Order must be either "Dispatched" or "Delivered" to set the order as "Returned"')
                        if sum(return_list) == True:
                            order = self.env['stock.picking'].search(
                                [('picking_type_code', '=', 'outgoing'),('unique_ref.unique_ref', '=', lines.unique_ref)],order='create_date desc',limit=1)
                            dic = {'invoiced_id': order.invoiced_id.id, 'invoice_date': order.invoice_date,
                                   'credit_note_number': order.credit_note_number.id,
                                   'credit_note_date': order.credit_note_date}
                            stock_return_picking = self.env['stock.return.picking'].create({'picking_id': order.id})
                            stock_return_picking._onchange_picking_id()
                            stock_return_picking_line = stock_return_picking.product_return_moves
                            stock_return_picking_line.update({
                                'quantity': order.move_ids_without_package.quantity_done
                            })
                            x = stock_return_picking.create_returns()
                            return_order = self.env['stock.picking'].search([('id', '=', x['res_id'])])
                            return_order.write(dic)
                            return_order.action_set_quantities_to_reservation()
                            return_order.button_validate()
                            order.return_order = return_order
                            unique_ref_searched.update({
                                'return_date': lines.return_date,
                                'return_reason': lines.return_reason,
                                'up_return_date': datetime.date.today()
                            })
                            unique_ref_searched.delivery_id.order_status = 'returned'  # changed
                            # lines.unlink()
                            delete.append(lines.id)
                    else:
                        raise UserError("BIW Unique Reference Number Doesn't exist")
                else:
                    raise UserError("Empty BIW Unique Reference Number")

            if self.to_update == 'cancelled':
                if lines.unique_ref:
                    if lines.unique_ref.strip() in awb_no:
                        if unique_ref_searched.order_status == 'wip' or unique_ref_searched.order_status == 'ready' or unique_ref_searched.order_status == 'not_serviceable' or unique_ref_searched.order_status == 'hand_off' or unique_ref_searched.order_status == 'returned':
                            if unique_ref_searched.order_status == 'wip' or unique_ref_searched.order_status == 'ready' or unique_ref_searched.order_status == 'not_serviceable':
                                if lines.cancel_date and lines.cancel_date >= unique_ref_searched.up_date.date():
                                    self.env['stock.picking'].search(
                                        [('unique_ref', '=', unique_ref_searched.unique_ref),
                                         ('picking_type_code', '=', 'outgoing')],order='create_date desc',limit=1).action_cancel()
                                    unique_ref_searched.update({
                                        'cancel_date': lines.cancel_date,
                                        'cancel_reason': lines.cancel_reason,
                                    })
                                    unique_ref_searched.delivery_id.order_status = 'cancelled'  # changed
                                    # lines.unlink()
                                    delete.append(lines.id)
                                else:
                                    raise UserError(
                                        'Date should be greater than or equal to Order upload Date')
                            if unique_ref_searched.order_status == 'hand_off':
                                if lines.cancel_date and lines.cancel_date >= unique_ref_searched.hand_off_date:
                                    self.env['stock.picking'].search(
                                        [('unique_ref', '=', unique_ref_searched.unique_ref),
                                         ('picking_type_code', '=', 'outgoing')],order='create_date desc',limit=1).action_cancel()
                                    unique_ref_searched.update({
                                        'cancel_date': lines.cancel_date,
                                        'cancel_reason': lines.cancel_reason,
                                    })
                                    unique_ref_searched.delivery_id.order_status = 'cancelled'  # changed
                                    # lines.unlink()
                                    delete.append(lines.id)
                                else:
                                    raise UserError('Date should be greater than or equal to hand-off Date')
                            if unique_ref_searched.order_status == 'returned':
                                if lines.cancel_date and lines.cancel_date > unique_ref_searched.up_return_date:
                                    #         # temporary -  for patch purpose, (Order returned in master sheet and manually updated the quantity to inventory, but status in delivery order still remains Dispatched "Done status" so upcoming orders will be erp flow untill 27/02/2023)
                                    if self.env['stock.picking'].search(
                                            [('unique_ref', '=', unique_ref_searched.unique_ref),
                                             ('picking_type_code', '=', 'outgoing')],order='create_date desc',limit=1).state == 'done':
                                        unique_ref_searched.update({
                                            'cancel_date': lines.cancel_date,
                                            'cancel_reason': lines.cancel_reason,
                                        })
                                        unique_ref_searched.delivery_id.order_status = 'cancelled'  # changed
                                        delete.append(lines.id)
                                    else:
                                        self.env['stock.picking'].search(
                                            [('unique_ref', '=', unique_ref_searched.unique_ref),
                                             ('picking_type_code', '=', 'outgoing')],order='create_date desc',limit=1).action_cancel()
                                        unique_ref_searched.update({
                                            'cancel_date': lines.cancel_date,
                                            'cancel_reason': lines.cancel_reason,
                                        })
                                        unique_ref_searched.delivery_id.order_status = 'cancelled'  # changed
                                        delete.append(lines.id)
                                else:
                                    raise UserError('Date should be greater than Return Date')
                        else:
                            raise UserError(
                                "Order must be either 'WIP', 'Ready', 'Not Serviceable', 'Hand-off' or 'Returned' to set the order as 'Cancelled'")
                    else:
                        raise UserError("BIW Unique Reference Number Doesn't exist")
                else:
                    raise UserError("Empty BIW Unique Reference Number")

            if self.to_update == 'returned_n_reshipped':  # To do this mapping customer(address_id_map) is must in master sheet
                if lines.unique_ref:
                    if lines.unique_ref.strip() in awb_no:
                        if unique_ref_searched.order_status == 'returned':
                            if datetime.date.today() and unique_ref_searched.up_return_date:  # bhjfjvhjvbhvbdvbhdsvbhdsvb should be uncommented and send..............................................................

                                tries_list = []
                                parent_awb = ''
                                if unique_ref_searched.parent_line.id == False:
                                    tries_list.append(0)
                                    parent_awb = unique_ref_searched
                                    company_ids.append(unique_ref_searched.customer_name.parent_id)
                                else:
                                    parent_awb = unique_ref_searched.parent_line
                                    company_ids.append(unique_ref_searched.parent_line.customer_name.parent_id)
                                    for recs in unique_ref_searched.parent_line.try_lines:
                                        tries_list.append(recs.try_no_type)

                                tries_available = []
                                for tries in self.env['multi.try'].search([]):
                                    tries_available.append(int(tries.type))

                                if int(max(tries_list)) < max(tries_available):
                                    new_try = self.env['multi.try'].search([('type', '=', str(int(max(tries_list)) + 1))])

                                    order = parent_awb.try_lines.create({
                                        'parent_line': parent_awb.id,
                                        'unique_ref': parent_awb.unique_ref,
                                        'file_name': parent_awb.file_name.id,
                                        'up_date': parent_awb.up_date,
                                        'ref_no': parent_awb.ref_no,
                                        'item_code': parent_awb.item_code,
                                        'item_desc': parent_awb.item_desc,
                                        'global_item_code': parent_awb.global_item_code.id,
                                        'qty': parent_awb.qty,
                                    })

                                    contact = parent_awb.customer_name.create({
                                        'unique_ref': order.id,
                                        'parent_id': parent_awb.customer_name.id,
                                        'type': 'delivery',
                                        'company_type': 'person',
                                        'tries': new_try.id,
                                        'name': lines.name,
                                        'street': lines.add1,
                                        'street2': lines.add2,
                                        'city': lines.city,
                                        'zip': lines.pin,
                                        'mobile': lines.phone,
                                        'email': lines.email
                                    })

                                    order.update({
                                        'customer_name': contact.id
                                    })

                                    created_retry_line.append(order)
                                    unique_ref_searched.delivery_id.order_status = 're_dispatched'

                                    vals.append((0, 0, {
                                        'product_id': parent_awb.global_item_code.id,
                                        'name': parent_awb.item_desc,
                                        'contact_name': contact.id,
                                        'product_uom_qty': parent_awb.qty
                                    }))
                                    delete.append(lines.id)

                                else:
                                    raise UserError('Maximum Try Reached: ' + str(max(tries_available)))
                            else:
                                raise UserError("Can't Re-Dispatch the orders which are returned Today")  # bhjfjvhjvbhvbdvbhdsvbhdsvb should be uncommented and send..............................................................
                        else:
                            raise UserError('Order must be "Returned" to Re-Dispatch the order')
                    else:
                        raise UserError("BIW Unique Reference Number Doesn't exist")
                else:
                    raise UserError("Empty BIW Unique Reference Number")

        if self.to_update == 'returned_n_reshipped':
            if len(set(company_ids)) == 1:
                new_sale_order = self.env['sale.order'].create({
                    'state': 'draft',
                    'partner_id': company_ids[0].id,
                    'order_line': vals
                })

                for re_orders in created_retry_line:
                    re_orders.order_no = new_sale_order.id
            else:
                raise UserError("Select orders which are Related to one Company")

        self.env['update.rec'].search([('id', 'in', delete)]).unlink()