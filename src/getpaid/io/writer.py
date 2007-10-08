
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

import interfaces

#ImportReader.register_type( )
ExportWriter.register_type( Message, "msgid")

# for property option objects
def getPropertyMap( self, interface ):
    d = {}
    for field in schema.getFields( interface ).values():
        value = field.query( self )
        # recurse into subobject fields
        if isinstance( field, schema.Object) and value is not None:
            value = getSchemaMap( value, field.schema )
            
        d[ field.__name__ ] = value
    return d
    
# 
def getSchemaMap( self,  interfaces=None):
    """
    generically introspects all schemas, and dumps them, recurses into children, and schema attribute objects
    """
    # duplicate fields get overwritten, first one in interface specification wins
    if interfaces is None:
        interfaces = list( interface.providedBy( self ) )
        interfaces.reverse()
    
    if not isinstance( interfaces, (list, tuple) ):
        interfaces = [ interfaces ]
    
    d = {}
    for i in interfaces:
        d.update( getPropertyMap( self, i ) )
        if issubclass( i, IContainer) and not 'contained' in d:
            children = [ (k, getSchemaMap(v) ) for k,v in self.items()]
            # sigh.. we loose ordering on ordered containers
            if children:
                d['contained'] = dict( children )
    return d
    
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
        properties = getSchemaMap( self.context, getpaid.core.interfaces.IOrder )
        writer.dumpDictionary( 'properties', properties )

        # dump audit log
        log = self.serializeAuditLog()
        writer.dumpList( 'log', log )
        
        writer.endElementNS( (None, 'order'), 'order')
        writer.close()

    def serializeAuditLog( self ):
        log_entries = []
        for entry in getpaid.core.interfaces.IOrderWorkflowLog( self.context ):
            state = getSchemaMap( entry, getpaid.core.interfaces.IOrderWorkflowEntry)
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
        settings = getPropertyMap( options, IGetPaidManagementOptions )        
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


