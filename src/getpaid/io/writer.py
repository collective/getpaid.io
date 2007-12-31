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


import tempfile, tarfile

import getpaid.core.interfaces

from ore.xd import ExportWriter, ImportReader

from zope.app.container.interfaces import IContainer
from zope import schema, component, interface
from zope.i18nmessageid.message import Message
from xml.sax.xmlreader import AttributesNSImpl

try:
    from Products.PloneGetPaid.interfaces import IGetPaidManagementOptions
except ImportError:
    class IGetPaidManagementOptions( interface.Interface ): pass

import interfaces, utils

ExportWriter.register_type( Message, "msgid")

class OrderExportWriter( object ):
    interface.implements( interfaces.IObjectExportWriter )

    def __init__( self, context ):
        self.context = context

    def exportToStream( self, stream ):
        writer = ExportWriter( stream )        

        attrs = AttributesNSImpl( {}, {} )

        # wrap data in enclosing element
        writer.startElementNS( (None, 'order'), 'order', attrs)
        
        # dump settings, recurses into subobjects
        properties = utils.getSchemaMap( self.context, getpaid.core.interfaces.IOrder )
        writer.dumpDictionary( 'properties', properties )

        # dump audit log
        log = self.serializeAuditLog()
        writer.dumpList( 'log', log )
        
        writer.endElementNS( (None, 'order'), 'order')
        writer.close()

    def serializeAuditLog( self ):
        log_entries = []
        for entry in getpaid.core.interfaces.IOrderWorkflowLog( self.context ):
            state = utils.getSchemaMap( entry, getpaid.core.interfaces.IOrderWorkflowEntry)
            log_entries.append( state )
        return log_entries
        
class StoreWriter( object ):
    
    interface.implements( interfaces.IStoreWriter )
    
    def __init__( self, store):
        self.store = store
    
    def toArchiveFile( self, file_path ):
        """
        places the contents of the archive into the given file path
        """
        stream = open( file_path, 'w')
        self.toArchiveStream( stream )
        
    def toArchiveStream( self ):
        """
        returns a stream to an archive file
        """
        stream = tempfile.TemporaryFile()
        tfile = tarfile.TarFile.open( mode='w|gz',  fileobj=stream )
        
        self.exportSettings( tfile )
        self.exportOrders( tfile )
        self.exportProducts( tfile )
        stream.seek(0,0)
        return stream

    def addStream( self, stream, tarfile, name ):
        stream.seek(0,0)
        info = tarfile.gettarinfo( fileobj=stream, arcname=name)
        tarfile.addfile( info, fileobj=stream)   

    def exportSettings( self, tarfile ):
        options = IGetPaidManagementOptions( self.store )
        settings = utils.getPropertyMap( options, IGetPaidManagementOptions )        
        stream = tempfile.TemporaryFile()
        try:
            writer = ExportWriter( stream )
            writer.dumpDictionary( 'settings', settings)
            writer.close()
            self.addStream( stream, tarfile, 'settings.xml' )
        finally:
            stream.close()
     
    def exportOrders( self, tarfile ):
        orders = component.getUtility(getpaid.core.interfaces.IOrderManager)
        
        for o in orders.storage.values():
            writer = interfaces.IObjectExportWriter( o )
            stream = tempfile.TemporaryFile()
            try:
                writer.exportToStream( stream )    
                self.addStream( stream, tarfile, 'orders/%s.xml'%o.order_id )
            finally:
                stream.close()

    def exportProducts( self, tarfile ):
        product_catalog = component.queryUtility(getpaid.core.interfaces.IProductCatalog, None)
        if product_catalog is None:
            return 
            
        for p in product_catalog:
            writer = interfaces.IObjectExportWriter( p )
            stream = tempfile.TemporaryFile()
            try:
                writer.exportToStream( stream )    
                self.addStream( stream, tarfile, 'products/%s.xml'%p.item )
            finally:
                stream.close()


