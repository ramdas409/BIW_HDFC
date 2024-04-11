# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _,SUPERUSER_ID
from datetime import datetime
from odoo.exceptions import ValidationError, UserError
import tempfile
import binascii
import xlrd
import os
import subprocess


class RollBackStock(models.Model):
    _inherit = 'stock.picking'

    def rollback_handoff(self):
        for rec in self:
            if(rec.order_status!="hand_off"):
                raise ValidationError('Roll Back can be done  for only  Hand Off orders')
            rec.awb_number.delivery_order_number_many=[(5,)]
            rec.awb_number=None
            rec.airport=""
            rec.hub=""
            rec.courier_company_id=None
            rec.hand_off_id=""
            rec.hand_off_date_time=False
            if rec.picking_type_code == 'outgoing':
                if rec.move_ids_without_package.forecast_availability == rec.move_ids_without_package.product_uom_qty:
                    if rec.state == 'assigned':  # Ready
                        rec.order_status = 'ready'
                else:
                    rec.order_status = 'wip'

class RollBackStockSale(models.Model):
    _inherit = 'sale.order'

    def rollback_entire_process(self):
        # for rec in self:
        #    stock_data=self.env['stock.picking'].search([('origin','=',rec.name),('awb_number','!=',None)])
        #    if(stock_data):
        #        raise ValidationError('Roll Back can be done  for Hand Off orders')
        #    fresh_orders=self.env['pemt.rec'].search([('order_no','=',rec.id)])
        #    print('fresh_orders',fresh_orders)
        #    fresh_orders.unlink()
        #    rec.unlink()

        for rec in self:
           stock_data = self.env['stock.picking'].search([('origin', '=', rec.name), ('awb_number', '!=', None)])
           if (stock_data):
               raise ValidationError('Roll Back can be done  for Hand Off orders')
           fresh_orders = self.env['pemt.rec'].search([('order_no', '=', rec.id)])
           fresh_orders.unlink()
           self.env['stock.picking'].search([('origin', '=', rec.name)]).unlink()
           rec.action_cancel()
           rec.unlink()


class GetGitCommit(models.Model):
    _name='github.commit'

    path=fields.Char(string="Path")
    commit_id=fields.Char(string="Commit Id")
    get_commit_id=fields.Boolean(String="Get Commit ID")
    pull_commit_id=fields.Boolean(String="Pull Commit ID")
    pull_commands=fields.Char(String='Pull ')
    error_log=fields.Char(sring="Error log")

    def get_commit_from_github_path(self):
        print('aaaaaaaaaaaaaaaaaaaaaaaaaaa')
        if (not self.pull_commit_id and not self.get_commit_id):
            raise ValidationError("Please select any one in  Get commit id or pull commit id but not empty")

        elif(self.pull_commit_id and self.get_commit_id):
            raise ValidationError("Please select any one in  Get commit id or pull commit id but not both")
        elif(self.get_commit_id):
        # print(os.getcwd())
            os.chdir(self.path)
            print(os.getcwd())
            result = subprocess.run('git rev-parse HEAD ', shell=True, capture_output=True, text=True)
            print(result.stdout)
            self.commit_id=result.stdout
        elif(self.pull_commit_id):
            os.chdir(self.path)
            print(os.getcwd())
            subprocess.run('git checkout {commit}'.format(commit=self.commit_id), shell=True, capture_output=True, text=True)
            # result=subprocess.run('git rev-parse HEAD ', shell=True, capture_output=True, text=True)
            # print(result.stdout)
            # self.commit_id = result.stdout
            # subprocess.run(self.pull_commands, shell=True, capture_output=True, text=True)
            print('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')


        # print(rec.name,'sale order nameeeeeeeeeeeeeeeeeeeeee')

