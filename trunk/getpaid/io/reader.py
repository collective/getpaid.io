from zope import interface, schema, component


class StoreReader( object ):
    
    interface.implements( interfaces.IStoreReader )
    
    def importArchiveFile( self, file_path ):
        """ 
        import the given archive file
        """
        
    def importArchiveStream( self, stream ):
        """
        import the archive stream
        """

    def importSettings( self, tarfile ):
        pass
        
    def importOrders( self, tarfile ):
        pass
        
    def importProducts( self, tarfile ):
        pass
        
    def readPath( self, tar_path ):
        pass
        
class OrderReader(object)

    def __init__( self, context ):
        self.context = context

    def importStream( self, stream ):
        ImportReader( stream )