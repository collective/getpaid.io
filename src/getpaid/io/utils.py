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
    extract properties from an object of the given zope schema, in a mapping by
    field schema.name, recurses into schema.Objects, returns a nested dictionary.
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
