#include <Python.h>
#include "Cart.h"

typedef struct {
    PyObject_HEAD
    CART **primaryCarts;
    CART **predictiveCarts;
    FeatureGroup *primaryFeatures;
    FeatureGroup *predictiveFeatures;
} QuillCKnowledge;

static PyTypeObject QuillCKnowledgeType = {
    PyObject_HEAD_INIT(NULL)
    0, "QuillCKnowledge", sizeof(QuillCKnowledge), 0,
};

static PyObject *QuillCKnowledgeGetClass( PyObject *_self, PyObject *args ) {
    const char *s = NULL;
    const char *type = NULL;
    int focus = -1;
    int multiple = -1;
    QuillCKnowledge *self = NULL;
    NodeClass *classes = NULL;
    int j = -1;
    PyObject *list;
    PyObject *resultStr;
    PyObject *frequency;
    PyObject *pair;
    CART **carts;
    FeatureGroup *featureGroup;

    if ( !PyArg_ParseTuple(args,"sisi:GetClass",&s,&focus,&type,&multiple) ) {
        return NULL;
    }
    self = (QuillCKnowledge *)_self;
    if ( strcmp(type,"predictive") == 0 ) {
        carts = self->predictiveCarts;
        featureGroup = self->predictiveFeatures;
    }
    else if ( strcmp(type,"primary") == 0 ) {
        carts = self->primaryCarts;
        featureGroup = self->primaryFeatures;
    }
    else {
        return NULL;
    }

    list = PyList_New( 0 );
    if ( !list ) return NULL;

    if ( !carts[(unsigned char)s[focus]] ) {
#if 0
        resultStr = PyUnicode_DecodeLatin1( s+focus, 1, NULL );
        //resultStr = PyString_FromFormat( "%c", (unsigned int)s[focus] );
        PyList_Append( list, resultStr );
        Py_DECREF( resultStr );
#endif
        fprintf( stderr, "Cart not found for '%c' from '%s'\n", (unsigned char)s[focus], s );
    }
    else {
        classes = LetterToClassLookup( featureGroup, carts[(unsigned char)s[focus]], s, focus, multiple );
        assert( classes );
        /*if ( !multiple ) {
            resultStr = PyUnicode_DecodeUTF8( classes[0], strlen(classes[0]), NULL );
            for ( j = 0; classes[j]; ++j ) {
                free( classes[j] );
            }
            free( classes );
            return resultStr;
        }*/
        for ( j = 0; classes[j].utf8Class; ++j ) {
            resultStr = PyUnicode_DecodeUTF8( classes[j].utf8Class, strlen(classes[j].utf8Class), NULL );
            frequency = PyFloat_FromDouble((double)classes[j].frequency);
            if ( !resultStr ) {
                resultStr = PyUnicode_DecodeLatin1( s+focus, 1, NULL );
                frequency = PyFloat_FromDouble(0.0);
                //resultStr = PyString_FromFormat( "%c", (unsigned int)s[focus] );
            }
            pair = PyTuple_Pack(2, resultStr, frequency);
            
            PyList_Append( list, pair );
            
            Py_DECREF( resultStr );
            Py_DECREF( frequency );
            Py_DECREF( pair );
        }
        /*
        for ( j = 0; classes[j]; ++j ) {
            free( classes[j] );
        }
        free( classes );
        */
    }
    return list;
};

static void CollectClasses( CART *node, PyObject *classes ) {
    int i;
    int longValue;
    if ( node->terminal ) {
        for ( i = 0; node->classes[i].utf8Class; ++i ) {
            PyObject *value = PyDict_GetItemString( classes, node->classes[i].utf8Class );
            if ( !value ) {
                PyDict_SetItemString( classes, node->classes[i].utf8Class, PyInt_FromLong(1) );
            }
            else {
                longValue = PyInt_AsLong( value );
                PyDict_SetItemString( classes, node->classes[i].utf8Class, PyInt_FromLong(longValue+1) );
            }
        }
    }
    else {
        CollectClasses( node->leftCART, classes );
        CollectClasses( node->rightCART, classes );
    }
}

static PyObject *QuillCKnowledgeGetAllClasses( PyObject *_self, PyObject *args ) {
    QuillCKnowledge *self = NULL;
    unsigned char nodeKey = -1;
    PyObject *classesList;
    CART **carts;

    if ( !PyArg_ParseTuple(args,"B:GetAllClasses",&nodeKey) ) {
        return NULL;
    }
    self = (QuillCKnowledge *)_self;
    carts = self->predictiveCarts;

    if ( !carts[nodeKey] ) {
        fprintf( stderr, "Cart not found for %c\n", nodeKey );
        return NULL;
    }

    classesList = PyDict_New();
    if ( !classesList ) return NULL;
    CollectClasses( carts[nodeKey], classesList );

    return classesList;
};

static PyObject *QuillCKnowledgeGetAllCartKeys( PyObject *_self, PyObject *args ) {
    QuillCKnowledge *self = NULL;
    PyObject *list;
    CART **carts;
    int i;

    self = (QuillCKnowledge *)_self;
    carts = self->predictiveCarts;

    list = PyList_New( 0 );
    if ( !list ) return NULL;

    for ( i = 0; i < 256; ++i ) {
        if ( !carts[i] ) continue;
        PyList_Append( list, PyInt_FromLong(i) );
    }
    return list;
};

static PyMethodDef quillCKnowledgeMethods[] = {
    { "GetClass", (PyCFunction)QuillCKnowledgeGetClass, METH_VARARGS },
    { "GetAllClasses", (PyCFunction)QuillCKnowledgeGetAllClasses, METH_VARARGS },
    { "GetAllCartKeys", (PyCFunction)QuillCKnowledgeGetAllCartKeys, METH_VARARGS },
    { NULL, NULL }
};

static PyObject *QuillCKnowledgeNew( PyTypeObject *type, PyObject *args, PyObject *kwargs ) {
    const char *fileName;
    QuillCKnowledge *knowledge;
    int i;

    if ( !PyArg_ParseTuple(args,"s",&fileName) ) {
        return NULL;
    }
    knowledge = (QuillCKnowledge *) type->tp_alloc( &QuillCKnowledgeType, 0 );
    if ( !knowledge ) {
        return NULL;
    }
    knowledge->primaryCarts = (CART **) malloc( sizeof(CART *) *256 );
    if ( !knowledge->primaryCarts ) {
        return NULL;
    }
    knowledge->predictiveCarts = (CART **) malloc( sizeof(CART *) *256 );
    if ( !knowledge->predictiveCarts ) {
        return NULL;
    }
    for ( i = 0; i < 256; ++i ) {
        knowledge->primaryCarts[i] = NULL;
        knowledge->predictiveCarts[i] = NULL;
    }

    knowledge->primaryFeatures = (FeatureGroup *) malloc( sizeof(FeatureGroup) );
    if ( !knowledge->primaryFeatures ) {
        return NULL;
    }
    knowledge->primaryFeatures->noOfFeatures = 0;
    knowledge->primaryFeatures->features = (Feature *) malloc( sizeof(Feature) );
    if ( !knowledge->primaryFeatures->features ) {
        return NULL;
    }
    knowledge->predictiveFeatures = (FeatureGroup *) malloc( sizeof(FeatureGroup) );
    if ( !knowledge->predictiveFeatures ) {
        return NULL;
    }
    knowledge->predictiveFeatures->noOfFeatures = 0;
    knowledge->predictiveFeatures->features = (Feature *) malloc( sizeof(Feature) );
    if ( !knowledge->predictiveFeatures->features ) {
        return NULL;
    }

    Py_BEGIN_ALLOW_THREADS
    LoadKnowledge( fileName, knowledge->primaryCarts, knowledge->predictiveCarts, knowledge->primaryFeatures, knowledge->predictiveFeatures );
    Py_END_ALLOW_THREADS

    return (PyObject *)knowledge;
}

static void QuillCKnowledgeDeAlloc( QuillCKnowledge *self ) {
    int i;
    for ( i = 0; i < 256; ++i ) {
        free( self->primaryCarts[i] );
        free( self->predictiveCarts[i] );
    } 
    free( self->primaryCarts );
    free( self->predictiveCarts );
    free( self->primaryFeatures );
    free( self->predictiveFeatures );
    self->ob_type->tp_free( (PyObject *) self );
}

static PyMethodDef quillCCartMethods[] = {
    { NULL, NULL, 0, NULL }
};

static int init_type( PyTypeObject *type, void *f_dealloc, const char *doc, PyMethodDef *methods, void *f_new ) {
    type->tp_dealloc = (destructor)f_dealloc;
    type->tp_flags = Py_TPFLAGS_DEFAULT;
    type->tp_doc = (char *)doc;
    type->tp_methods = methods;
    type->tp_new = (newfunc)f_new;
    return PyType_Ready(type);
}

PyMODINIT_FUNC initQuillCCart( void ) {
    int result;
    PyObject *module = Py_InitModule( "QuillCCart", quillCCartMethods );
    result = init_type( &QuillCKnowledgeType, QuillCKnowledgeDeAlloc, "Quill Knowledge object", quillCKnowledgeMethods, QuillCKnowledgeNew );
    if ( result < 0 ) {
        return;
    }
    Py_INCREF( &QuillCKnowledgeType );
    PyModule_AddObject( module, "QuillCKnowledge", (PyObject *)&QuillCKnowledgeType );
}
