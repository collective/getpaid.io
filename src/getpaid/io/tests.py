"""Doc test runner
"""

__docformat__ = "reStructuredText"

import doctest
import unittest

from StringIO import StringIO

from zope.testing.doctestunit import DocFileSuite
from zope.app.testing import placelesssetup, ztapi
from zope.app.annotation import interfaces as annotation_interfaces
from zope.app.annotation import attribute

from hurry.workflow import interfaces

import random, string, datetime

from zope import component
from xml.sax import make_parser
from ore.xd import ImportReader

from getpaid.io import writer
from getpaid.io.interfaces import IStoreWriter, IObjectExportWriter
from getpaid.core.interfaces import IOrder, IOrderManager, IOrderWorkflowLog, workflow_states
from getpaid.core import order, cart, item as lineitem
from getpaid.core.workflow import store, order as oworkflow

class OrderImportTests( unittest.TestCase ):

    def setUp( self ):
        placelesssetup.setUp()
        coreSetUp( None )
        self.orders = list( createOrders() )        
        self.manager = component.getUtility( IOrderManager )
                    
    def tearDown( self ):
        placelesssetup.tearDown()

class OrderExportTests( unittest.TestCase ):

    def setUp( self ):
        placelesssetup.setUp()
        coreSetUp( None )
        self.orders = list( createOrders() )
        self.manager = component.getUtility( IOrderManager )
        
    def tearDown( self ):
        placelesssetup.tearDown()
        self.orders = None
        self.manager = None
        
    def testOrderExport( self ):
        
        for o in self.orders:
            stream = StringIO()
            writer = IObjectExportWriter( o )
            writer.exportToStream( stream )
            serialized = stream.getvalue()
            parser = make_parser()
            reader = ImportReader()
            parser.setContentHandler( reader )
            stream.seek(0,0)
            parser.parse( stream )
            data = reader.getData()
            self.assertEqual( len(data['order']['properties']['shopping_cart']['contained']), len( o.shopping_cart ) )

            

def createOrders( how_many=10 ):
    manager = component.getUtility( IOrderManager )

    for i in range(1, how_many):
        o = order.Order()
        o.order_id = str(i)

        o.shopping_cart = sc = cart.ShoppingCart()

        for i in range(0, 10):
            item = lineitem.LineItem()
            item.name = "p%s"%random.choice( string.letters )
            item.quantity = random.randint(1,25)
            item.cost = random.randint(30, 100)
            item.item_id = "i%s"%random.choice( string.letters )
            if item.item_id in sc:
                continue
            sc[item.item_id] = item

        o.user_id = "u%s"%random.choice( string.letters )
        o.finance_workflow.fireTransition('create')
        o.fulfillment_workflow.fireTransition('create')

        manager.store( o )

        yield o
    
def coreSetUp(doctest):
    placelesssetup.setUp()

    ztapi.provideAdapter( IOrder,
                          interfaces.IWorkflowState,
                          oworkflow.FinanceState,
                          'order.finance')

    ztapi.provideAdapter( IOrder,
                          interfaces.IWorkflowState,
                          oworkflow.FulfillmentState,
                          'order.fulfillment')

    ztapi.provideAdapter( IOrder,
                          interfaces.IWorkflowInfo,
                          oworkflow.FinanceInfo,
                          'order.finance')

    ztapi.provideAdapter( IOrder,
                     interfaces.IWorkflowInfo,
                     oworkflow.FulfillmentInfo,
                    'order.fulfillment')
                    
    ztapi.provideAdapter(annotation_interfaces.IAttributeAnnotatable,
                         annotation_interfaces.IAnnotations,
                         attribute.AttributeAnnotations)
                         
    ztapi.provideAdapter( IOrder, IObjectExportWriter, writer.OrderExportWriter)
    
    ztapi.provideAdapter( IOrder, IOrderWorkflowLog, order.OrderWorkflowLog )

    ztapi.provideUtility(interfaces.IWorkflow,
                         oworkflow.FulfillmentWorkflow(),
                        'order.fulfillment')
                        
    ztapi.provideUtility(interfaces.IWorkflow,
                        oworkflow.FinanceWorkflow(),
                        'order.finance')

    ztapi.provideUtility(interfaces.IWorkflowVersions,
                         store.StoreVersions())
    
    ztapi.provideUtility( IOrderManager, order.OrderManager() )
    

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite( OrderExportTests ),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
