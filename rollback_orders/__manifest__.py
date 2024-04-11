{
    'name': 'Roll back orders',
    'version': '15.0.0.0',
    'license': 'LGPL-3',
    'author': 'PMCPL',
    'category': 'sales',
    'website': 'http://int.primeminds.co/',
    'summary': 'Rollback orders  for any modifications for orders',
    'sequence': 10,
    'description': """""",
    'depends': ['base', 'stock','sale_stock','sale'],
    'data': ['security/ir.model.access.csv',
             'views/Rollback.xml'

             ],
    'installable': True,
    'application': False,
    'auto_install': False,
}