
import tempfile, tarfile

import getpaid.core.interfaces
from ore.xd import ExportWriter
from zope import schema, component, interface

from Products.PloneGetPaid.interfaces import IGetPaidManagementOptions

import interfaces
# for property option objects
def getPropertyMap( self, interface=None ):
    interface = interface or self.interface
    d = {}
    for field in schema.getFields( interface ):
        value = field.get( self )
        d[ field.__name__ ] = value
    return d


    
class OrderExportWriter( object ):
    interface.implements( interfaces.IObjectExportWriter )

    def exportToStream( self, stream ):
        writer = ExportWriter( stream )        
        state = getPropertyMap( self.context, getpaid.core.interfaces.IOrder )
        writer.dumpDictionary( 'properties', state )
        log = self.serializeAuditLog()
        writer.dumpList( 'log', log )
        writer.close()

    def serializeAuditLog( self, stream):
        log_entries = []
        for entry in getpaid.core.interfaces.IOrderWorkflowLog( self.context ):
            state = getPropertyMap( entry, getpaid.core.interfaces.IOrderWorkflowEntry)
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
        stream = tempfile.mktempfile()
        tarfile = tarfile.TarFile( stream )
        
        self.exportSettings( tarfile )
        self.exportOrders( tarfile )
        self.exportProducts( tarfile )
        

    def addStream( self, stream, tarfile, name ):
        stream.seek(0,0)
        info = tarfile.gettarinfo( stream, name)
        tarfile.addfile( info, stream)   

    def exportSettings( self, tarfile ):
        options = IGetPaidManagementOptions( self.store )
        settings = getPropertyMap( options )        
        stream = tempfile.mktemp()
        try:
            writer = ExportWriter( stream )
            writer.dumpDictionary( 'settings', settings)
            writer.close()
            self.addStream( stream, 'settings.xml' )
        finally:
            stream.close()
     
    def exportOrders( self, tarfile ):
        orders = component.getUtility(getpaid.core.interfaces.IOrderManager)
        
        for o in orders:
            writer = interfaces.IObjectExportWriter( o )
            stream = tempfile.mktempfile()
            try:
                writer.exportToStream( stream )    
                self.addStream( stream, 'orders/%s.xml'%o.order_id )
            finally:
                stream.close()

    def exportProducts( self, tarfile ):
        product_catalog = component.getUtility(getpaid.core.interfaces.IProductCatalog)
        for p in product_catalog:
            writer = interfaces.IObjectExportWriter( p )
            stream = tempfile.mktempfile()
            try:
                writer.exportToStream( stream )    
                self.addStream( stream, 'products/%s.xml'%p.item )
            finally:
                stream.close()


