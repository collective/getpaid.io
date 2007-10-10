from zope import interface, schema
from zope.app.container.interfaces import IContainer


# an important notional difference, read apis are recursive, write apis are not, and do not create children

def setPropertyMap( self, interface, values ):
    """
    given an object, a schema, and a mapping of values set the given values
    on the object using the schema fields.
    """
    for name, field in schema.getFields( interface ).items():
        v = values.get( name )
        if not v:
            continue
        if field.readonly:
            setattr( self, name, v )
        else:
            field.set( self, v )

def getPropertyMap( self, interface ):
    """ 
    extract properties from an object of the given zope schema, in key/value form
    and schema.Object attributes, returns a nested dictionary.
    """
    d = {}
    for field in schema.getFields( interface ).values():
        if field.__name__.startswith('__'):
            continue
        value = field.query( self )
        # recurse into subobject fields
        if isinstance( field, schema.Object) and value is not None:
            value = getSchemaMap( value, field.schema )
            
        d[ field.__name__ ] = value
    return d
    
def setSchemaMap( self, values, interfaces=None):
    # duplicate fields get overwritten, first one in interface specification wins
    if interfaces is None:
        interfaces = list( interface.providedBy( self ) )
        interfaces.reverse()
    
    if not isinstance( interfaces, (list, tuple) ):
        interfaces = [ interfaces ]    
        
    for i in interfaces:
        setPropertyMap( self, i, values )

            
def getSchemaMap( self,  interfaces=None):
    """
    generically introspects all schemas of an object and serialize them to a dictionary, 
    recurses into zope3 containers, and uses getPropertyMap for serialization of values
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
