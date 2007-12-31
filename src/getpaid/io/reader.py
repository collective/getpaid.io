# Copyright (c) 2007 ifPeople, Kapil Thangavelu, and Contributors
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.


import tarfile, gzip
from xml.sax import make_parser

from zope import interface, component
from zope.i18nmessageid.message import Message

from ore.xd import ImportReader

import getpaid.core.interfaces
from getpaid.core import order, item, cart, payment
from getpaid.io import utils, interfaces

ImportReader.register_type( "msgid", Message )

def extractStream( stream ):
    parser = make_parser()
    reader = ImportReader()
    parser.setContentHandler( reader )
    parser.parse( stream )
    return reader.getData()
    
class TarListing( object ):
    __slots__ = ('_data',)
    def __init__(self, names):
        self._data = {}
        for n in names:
            self.add( n )
    def add( self, name ):
        segments = name.split('/')
        for i in range( 1, len(segments) ):
            dpath = '/'.join( segments[:i] )
            if not dpath:
                dpath = '/'
            if dpath in self._data:
                entries = self._data.get( dpath )
            else:
                entries = self._data.setdefault( dpath, [] )
            if not segments[i] in entries:
                entries.append( segments[i] )
                
    def listDirectory( self, dpath ):
        return iter( self._data.get( dpath, () ) )    
    
    def dir( self, dpath ):
        return [ '/'.join((dpath,x)) for x in  self._data.get( dpath, () )]
        
class StoreReader( object ):
    
    interface.implements( interfaces.IStoreReader )
    
    def __init__( self, context ):
        self.context = context
    
    def importArchiveFile( self, file_path ):
        """ 
        import the given archive file
        """
        fh = open( file_path )
        self.importArchiveStream( fh )
        
    def importArchiveStream( self, stream ):
        """
        import the archive stream
        """
        gzip_stream = gzip.GzipFile( fileobj=stream )
        self.archive = tarfile.TarFile( 'store-archive', 'r', gzip_stream )
        self.listing = TarListing( self.archive.getnames() )
        
        self.importSettings()
        self.importOrders()
        self.importProducts()

    def importSettings( self ):
        data = extractStream( self.readPath( 'settings.xml' ) )
        utils.setSchemaMap( self.context, data )
        
    def importOrders( self ):
        order_manager = component.getUtility( getpaid.core.interfaces.IOrderManager )
        for file_name, order_stream in self.readDirectory( 'orders'):
            oid = file_name[len('orders/'):-4]
            
            if order_manager.get(oid) is not None:
                continue
                
            o = order.Order()
            o.order_id = oid
            
            reader = interfaces.IObjectImportReader( o )
            reader.importStream( order_stream )
            order_manager.store( o )
            
    def importProducts( self ):
        product_catalog = component.getUtility( getpaid.core.interfaces.IProductCatalog )
        for file_name, product_stream in self.readDirectory('products'):
            pass

    def readPath( self, tar_path ):
        archive_member = self.archive.getmember( tar_path ) 
        return self.archive.extractfile( archive_member )

    def readDirectory( self, tar_path ):
        return [ ( p, self.readPath( p ) ) for p in self.listing.dir( tar_path ) ]
        
class OrderReader(object):

    interface.implements( interfaces.IObjectImportReader )
    
    def __init__( self, context ):
        self.context = context

    def importStream( self, stream ):
        data = extractStream( stream )['order']
        
        # setup object properties in the data and then set all properties on the order
        data['properties']['shopping_cart'] = self.importCart( data['properties']['shopping_cart']['contained'] )
        data['properties']['billing_address'] = self.importBillingAddress( data['properties']['billing_address'] )
        data['properties']['shipping_address'] = self.importShippingAddress( data['properties']['shipping_address'] )
        data['properties']['contact_information'] = self.importContactInformation( data['properties']['contact_information'] )
        utils.setSchemaMap( self.context, data['properties'] )
        
        self.importWorkflowLog( data['log'] )        
    
    def importCart( self, cart_items ):
        items = cart.ShoppingCart()
        for k, i in cart_items.items():
            line_item = item.LineItem()
            utils.setSchemaMap( line_item, i )
            items[ k ] = line_item
        return items

    def importBillingAddress( self, data ):        
        if not data: return
        address = payment.BillingAddress()
        utils.setSchemaMap( address, data)
        return address
        
    def importShippingAddress( self, data ):
        if not data: return        
        address = payment.ShippingAddress()
        utils.setSchemaMap( address, data)
        return address

    def importContactInformation( self, data ):
        if not data: return        
        info = payment.ContactInformation()
        utils.setSchemaMap( info, data)
        return info
        
    def importWorkflowLog( self, log_entries):
        log = getpaid.core.interfaces.IOrderWorkflowLog( self.context )
        log_entries.reverse()
        
        for e in log_entries:
            entry = order.OrderWorkflowRecord()
            utils.setSchemaMap( entry, e )
            log.add( entry )
