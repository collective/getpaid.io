"""
$Id$

"""
from zope import interface, schema

class IStoreWriter( Interface ):
    
    def toArchiveFile( file_path ):
        """
        places the contents of the archive into the given file path
        """
        
    def toArchiveStream( ):
        """
        returns a stream to an archive file
        """

class IStoreReader( Interface ):
    
    def importArchiveFile( file_path ):
        """ 
        import the given archive file
        """
        
    def importArchiveStream( stream ):
        """
        import the archive stream
        """
        
class IObjectExportWriter( interface.Interface ):
    
    def exportToStream( stream ):
        """
        """
                
class IFileExporter( Interface ):
    
    def exportString( ):
        """ """
        
    def exportStream( ):
        """ """

class IFileImporter( Interface ):
    
    def importStream( stream ):
        """ import the file stream """
    
    def importPath( file_path ):
        """ import the file path """
    