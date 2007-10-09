"""Doc test runner
"""

__docformat__ = "reStructuredText"


import unittest

from StringIO import StringIO
from xml.sax import make_parser

from zope import component
from zope.app.testing import ztapi
from ore.xd import ImportReader

from getpaid.io import writer, reader
from getpaid.io.interfaces import IObjectExportWriter, IObjectImportReader

from getpaid.core import order
from getpaid.core.interfaces import IOrder, IOrderManager
from getpaid.core.tests import base

class OrderImportExportTests( base.GetPaidTestCase ):

    def setUp( self ):
        super( OrderImportExportTests, self).setUp()
        self.orders = list( base.createOrders() )
        self.manager = component.getUtility( IOrderManager )
        ztapi.provideAdapter( IOrder, IObjectExportWriter, writer.OrderExportWriter)
        ztapi.provideAdapter( IOrder, IObjectImportReader, reader.OrderReader)        
        
    def tearDown( self ):
        super( OrderImportExportTests, self).tearDown()
        self.orders = None
        self.manager = None
        
    def testOrderExportImport( self ):
        # verify import and exporting orders across set of orders, sanity checking along the way 
        for o in self.orders:
            # first serialize the order
            stream = StringIO()
            writer = IObjectExportWriter( o )
            writer.exportToStream( stream )
            serialized = stream.getvalue()
            
            # next deserialize the data and sanity check it
            parser = make_parser()
            reader = ImportReader()
            parser.setContentHandler( reader )
            stream.seek(0,0)
            parser.parse( stream )
            data = reader.getData()
            self.assertEqual( len(data['order']['properties']['shopping_cart']['contained']), len( o.shopping_cart ) )

            # next import the order
            stream.seek(0, 0)
            oi = order.Order()
            reader = IObjectImportReader( oi )
            reader.importStream( stream )            
            
            # next verify that the imported order serialization is equivalent to the originals
            test_stream = StringIO()
            writer = IObjectExportWriter( oi ) 
            writer.exportToStream( test_stream )
            self.assertEqual( len(serialized), len(test_stream.getvalue()) )
            

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite( OrderImportExportTests ),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
