#include "stdio.h"
#include "string.h"
#include "assert.h"
#include "Cart.h"

#define XML_STATIC
#include <expat.h> 

#define XML_CHUNK_SIZE 8192*4

#define TREE_TYPE_PRIMARY 0
#define TREE_TYPE_PREDICTIVE 1

char *GetLatin1FromLatin1Utf8( const char *input ) {
    size_t i;
    unsigned char c;
    size_t len = strlen( input );
    char *s = (char *)calloc( len+1, sizeof(char) );
    int outputSize = 0;
    for ( i = 0; i < len; ++i ) {
        if ( (input[i]>>7) == 0 ) {
            c = input[i];
        }
        else {
            if ( i == (len-1) ) {
                fprintf( stderr, "Unsupported latin1Utf8 string passed '%s'\n", input );
                return s;
            }
            c = ((input[i]&3)<<6) | (input[i+1]&63);
            ++i;
        }
        s[outputSize] = c;
        ++outputSize;
    }
    return s;
}

typedef struct {
    char *elementData;
    int totalElementSize;
    int curElementSize;
    CART *root;
    CART *node;
    int treeType;
    unsigned char key;
    FeatureGroup *primaryFeatures;
    FeatureGroup *predictiveFeatures;
} XMLParserData;

static void XMLCALL XMLParsingStart( void *data, const char *element, const char **attr ) {
    XMLParserData *parserData = (XMLParserData *)data;
    sprintf( parserData->elementData, "" );
    parserData->curElementSize = 0;
    XMLAttrsRead( data, element, attr );
}

static void XMLCALL XMLParsingEnd( void *data, const char *element ) {
    XMLParserData *parserData = (XMLParserData *)data;
    if ( parserData->curElementSize+1 > parserData->totalElementSize ) {
        parserData->elementData = (char *)realloc( parserData->elementData, sizeof(char)*parserData->curElementSize+1 );
        assert( parserData->elementData );
        parserData->totalElementSize = parserData->curElementSize + 1;
    }
    parserData->elementData[parserData->curElementSize] = 0;
    XMLElementRead( data, element, parserData->elementData );
    sprintf( parserData->elementData, "" );
    parserData->curElementSize = 0;
}

static void XMLCALL XMLCharHandler( void *data, const XML_Char *s, int len ) {
    XMLParserData *parserData = (XMLParserData *)data;
    if ( parserData->curElementSize+len > parserData->totalElementSize ) {
        parserData->elementData = (char *)realloc( parserData->elementData, sizeof(char)*parserData->curElementSize+len );
        assert( parserData->elementData );
        parserData->totalElementSize = parserData->curElementSize + len;
    }
    memcpy( parserData->elementData+parserData->curElementSize, s, len );
    parserData->curElementSize += len;
}

void XMLElementRead( void *data, const char *element, const char *elementData ) {
    XMLParserData *parserData = (XMLParserData *)data;
    if ( strcmp(element,"QuillLanguage") == 0 ) {
        //nothing to do
    }
    else if ( strcmp(element,"tree") == 0 ) {
        //nothing to do
    }
    else if ( strcmp(element,"node") == 0 ) {
        if ( parserData->root != parserData->node ) {
            AddBinaryNode( parserData->root, parserData->node );
        }
    }
    else if ( strcmp(element,"split-rule") == 0 ) {
        // nothing to do
    }
    else if ( strcmp(element,"rel-index") == 0 ) {
        parserData->node->splitRule.relativeIndex = atoi( elementData );
    }
    else if ( strcmp(element,"context-id") == 0 ) {
        // nothing to do
    }
    else if ( strcmp(element,"feature") == 0 ) {
        SetNodeFeature( parserData->node, (parserData->treeType==TREE_TYPE_PREDICTIVE)?parserData->predictiveFeatures:parserData->primaryFeatures, GetLatin1FromLatin1Utf8(elementData) );
    }
    else if ( strcmp(element,"context-len") == 0 ) {
        // parserData->node->contextLength = atoi( elementData );
    }
    else if ( strcmp(element,"terminal") == 0 ) {
        if ( strcmp(elementData,"True") == 0 ) {
            parserData->node->terminal = 1;
        }
        else if ( strcmp(elementData,"False") == 0 ) {
            parserData->node->terminal = 0;
        }
        else {
            assert( !"Invalid terminal data" );
        }
    }
    else if ( strcmp(element,"classes") == 0 ) {
        if ( parserData->node->terminal ) {
            SetNodeClasses( parserData->node, elementData );
        }
    }
    else {
        assert( element );
        assert( !element );
    }
}

void XMLAttrsRead( void *data, const char *element, const char **attr ) {
    XMLParserData *parserData = (XMLParserData *)data;
    int i;
    if ( strcmp(element,"node") == 0 ) {
        if ( parserData->root->nodeID == -1 ) {
            parserData->node = parserData->root;
        }
        else {
            parserData->node = CARTNode( -1, -1, NULL, 0, NULL );
            assert( parserData->node );
        }
        for ( i = 0; attr[i]; i += 2 ) {
            if ( strcmp(attr[i],"id") == 0 ) {
                parserData->node->nodeID = atoi( attr[i+1] );
            }
            else {
                assert( 0 );
            }
        }
    }
    else if ( strcmp(element,"rel-index") == 0 ) {
        // nothing to do
    }
    else if ( strcmp(element,"context-id") == 0 ) {
        // nothing to do
    }
    else if ( strcmp(element,"feature") == 0 ) {
        // nothing to do
    }
    else if ( strcmp(element,"context-len") == 0 ) {
        // nothing to do
    }
    else if ( strcmp(element,"terminal") == 0 ) {
        // nothing to do
    }
    else if ( strcmp(element,"classes") == 0 ) {
        // nothing to do
    }
    else if ( strcmp(element,"tree") == 0 ) {
        for ( i = 0; attr[i] ; i += 2 ) {
            if ( strcmp(attr[i],"key") == 0 ) {
                parserData->key = GetLatin1FromLatin1Utf8(attr[i+1])[0];
            }
            else if ( strcmp(attr[i],"type") == 0 ) {
                if ( strcmp(attr[i+1],"predictive") == 0 ) {
                    parserData->treeType = TREE_TYPE_PREDICTIVE;
                }
                else if ( strcmp(attr[i+1],"primary") == 0 ) {
                    parserData->treeType = TREE_TYPE_PRIMARY;
                }
                else {
                    assert( 0 );
                }
            }
        }
    }
    else if ( strcmp(element,"QuillLanguage") == 0 ) {
        //assert( 0 );
    }
}

XMLParserData *NewXMLParserData( CART *root, FeatureGroup *primaryFeatures, FeatureGroup *predictiveFeatures ) {
    XMLParserData *parserData = (XMLParserData *) malloc( sizeof(XMLParserData) );
    parserData->totalElementSize = 256;
    parserData->curElementSize = 0;
    assert( parserData );
    parserData->elementData = (char *)calloc( parserData->totalElementSize, sizeof(char) );
    assert( parserData->elementData );
    parserData->root = root;
    parserData->node = NULL;
    parserData->primaryFeatures = primaryFeatures;
    parserData->predictiveFeatures = predictiveFeatures;
    return parserData;
}

void FreeXMLParserData( XMLParserData *parserData ) {
    free( parserData->elementData );
}

CART *CARTNode( int nodeID, int contextLength, char *featureStr, char terminal, NodeClass *classes ) {
    CART *node = (CART *) malloc( sizeof(CART) );
    node->nodeID = nodeID;
    // node->contextLength = contextLength;
    node->terminal = terminal;
    // Not using featureStr and classes
    node->leftCART = NULL;
    node->rightCART = NULL;
    node->splitRule.featureID = NULL;
    node->classes = NULL;
    return node;
}

void SetNodeClasses( CART *node, const char *classesStr ) {
    int noOfClasses = 1;
    int i;
    int lengthOfString = (int)strlen( classesStr );  // To verify that the classesStr wouldn't have a NULL char
    int startOfClass = -1;
    int endOfClass = -1;
    int startOfFrequency = -1;
    int endOfFrequency = -1;
    char num[16];

    node->classes = (NodeClass *)malloc( sizeof(NodeClass) * noOfClasses );
    node->classes[noOfClasses-1].utf8Class = NULL;
    node->classes[noOfClasses-1].frequency = -1;

    for ( i = 0; i < lengthOfString; ++i ) {
        if ( classesStr[i] == '"' ) {
            if ( startOfClass == -1 ) {
                startOfClass = i;
            }
            else if ( endOfClass == -1 ) {
                endOfClass = i;
            }
            else {
                assert( 0 );
            }
            if ( (startOfClass!=-1) && (endOfClass!=-1) ) {
                node->classes[noOfClasses-1].utf8Class = (char *) malloc( sizeof(char) * (endOfClass-startOfClass) );
                assert( node->classes[noOfClasses-1].utf8Class );
                memcpy( node->classes[noOfClasses-1].utf8Class, classesStr+startOfClass+1, endOfClass-startOfClass-1 );
                node->classes[noOfClasses-1].utf8Class[endOfClass-startOfClass-1] = 0;
            }
        }
        else if ( (classesStr[i]==',') || (classesStr[i]==')') ) {
            if ( startOfClass != -1 ) {
                assert( endOfClass != -1 );
                if ( startOfFrequency == -1 ) {
                    startOfFrequency = i;
                }
                else if ( endOfFrequency == -1 ) {
                    endOfFrequency = i;
                }
                else {
                    assert( 0 );
                }
                if ( (startOfFrequency!=-1) && (endOfFrequency!=-1) ) {
                    memcpy( num, classesStr+startOfFrequency+1, endOfFrequency-startOfFrequency-1 );
                    assert( (endOfFrequency-startOfFrequency-1) < 16 );
                    num[endOfFrequency-startOfFrequency-1] = 0;
                    node->classes[noOfClasses-1].frequency = atoi( num );
                    startOfClass = -1; endOfClass = -1;
                    startOfFrequency = -1; endOfFrequency = -1;
                    ++noOfClasses;
                    node->classes = (NodeClass *) realloc( node->classes, sizeof(NodeClass) * noOfClasses );
                    node->classes[noOfClasses-1].utf8Class = NULL;
                    node->classes[noOfClasses-1].frequency = -1;
                }
            }
        }
    }
    assert( node->classes[noOfClasses-1].utf8Class == NULL );
    assert( (startOfClass==-1) && (endOfClass==-1) && (startOfFrequency==-1) && (endOfFrequency==-1) );
}

void SetNodeFeature( CART *node, FeatureGroup *featureGroup, const char *featureStr ) {
    int i;
    int endOfKey = -1;
    int startOfKey = -1;
    int startOfWord = -1;
    int endOfWord = -1;
    int lengthOfString = (int)strlen( featureStr );
    int noOfTokens = 1;
    Feature *feature;

    i = ((int)strlen(featureStr)) - 1;
    for ( ; i >= 0; --i ) {
        if ( featureStr[i] == '\'') {
            if ( endOfKey == -1) {
                endOfKey = i;
            }
            else if ( startOfKey == -1 ) {
                startOfKey = i;
            }
            else {
                assert( 0 );
            }
            if ( (endOfKey!=-1) && (startOfKey!=-1) ) break;
        }
    }
    if ( (endOfKey==-1) || (startOfKey==-1) || (endOfKey==startOfKey) ) {
        node->splitRule.featureID = (char *) malloc( sizeof(char) );
        node->splitRule.featureID[0] = 0;
        return;
    }
    node->splitRule.featureID = (char *) malloc( sizeof(char) * (endOfKey-startOfKey) );
    memcpy( node->splitRule.featureID, featureStr+startOfKey+1, endOfKey-startOfKey-1 );
    node->splitRule.featureID[endOfKey-startOfKey-1] = 0;

    for ( i = 0; i < featureGroup->noOfFeatures; ++i ) {
        if ( strcmp(featureGroup->features[i].featureID,node->splitRule.featureID) == 0 ) {
            // current feature id already present in the FeatureGroup. Nothing to do
            return;
        }
    }

    ++featureGroup->noOfFeatures;
    featureGroup->features = (Feature *) realloc( featureGroup->features, sizeof(Feature)*featureGroup->noOfFeatures );
    assert( featureGroup->features );

    feature = &(featureGroup->features[featureGroup->noOfFeatures-1]);
    feature->featureID = strdup( node->splitRule.featureID );
    feature->featureTokens = (char **) malloc( sizeof(char *) * noOfTokens );
    feature->featureTokens[noOfTokens-1] = 0;
    for ( i = 0; i < lengthOfString; ++i ) {
        if ( featureStr[i] == '\'' ) {
            if ( startOfWord == -1 ) {
                startOfWord = i;
            }
            else if ( endOfWord == -1 ) {
                endOfWord = i;
            }
            else {
                assert( 0 );
            }
            if ( (startOfWord!=-1) && (endOfWord!=-1) ) {
                if ( startOfWord == startOfKey ) break;
                feature->featureTokens[noOfTokens-1] = (char *)malloc( sizeof(char) * (endOfWord-startOfWord) );
                memcpy( feature->featureTokens[noOfTokens-1], featureStr+startOfWord+1, endOfWord-startOfWord-1 );
                feature->featureTokens[noOfTokens-1][endOfWord-startOfWord-1] = 0;
                ++noOfTokens;
                feature->featureTokens = (char **)realloc( feature->featureTokens, sizeof(char*) * noOfTokens );
                assert( feature->featureTokens );
                feature->featureTokens[noOfTokens-1] = 0;
                startOfWord = -1;
                endOfWord = -1;
            }
        }
    }
}

void AddBinaryNode( CART *treeNode, CART *node ) {
    if ( node->nodeID < treeNode->nodeID ) {
        if ( treeNode->leftCART == NULL ) {
            treeNode->leftCART = node;
            return;
        }
        AddBinaryNode( treeNode->leftCART, node );
    }
    else {
        if ( treeNode->rightCART == NULL ) {
            treeNode->rightCART = node;
            return;
        }
        AddBinaryNode( treeNode->rightCART, node );
    }
}

int Match( FeatureGroup *featureGroup, CART *treeNode, const CARTWord *cartWord ) {
    int i, j;
    int realIndex;
    int lengthOfWord;
    char *word;
    int returnValue;
    word = (char *) malloc( sizeof(char) + sizeof(char)*strlen(cartWord->word)+ sizeof(char) +1 );
    assert( word );
    sprintf( word, "#%s_", cartWord->word );
    lengthOfWord = (int)strlen( word );

    realIndex = cartWord->focus + treeNode->splitRule.relativeIndex + 1;
    if ( (realIndex<0) || (realIndex>(int)strlen(word)) ) {
        returnValue = 0;
        goto freeMemAndReturn;
    }
    for ( i = 0; i < featureGroup->noOfFeatures; ++i ) {
        if ( strcmp(featureGroup->features[i].featureID,treeNode->splitRule.featureID) == 0 ) {
            for ( j = 0; featureGroup->features[i].featureTokens[j]; ++j ) {
                char *feature = featureGroup->features[i].featureTokens[j];
                if ( !strlen(feature) ) continue;
                if ( (realIndex+strlen(feature)) <= (size_t)lengthOfWord ) {
                    if ( memcmp(word+realIndex,feature,strlen(feature)) == 0 ) {
                        returnValue = 1;
                        goto freeMemAndReturn;
                    }
                }
            }
            break;
        }
    }
    returnValue = 0;
freeMemAndReturn :
    free( word );
    return returnValue;
}

CART *BuildTree( const char *fileName, int *treeType, char *key, FeatureGroup *primaryFeatures, FeatureGroup *predictiveFeatures ) {
    FILE *INPUTFILE = fopen( fileName, "rb" );

    XML_Parser p = XML_ParserCreate( NULL );
    CART *cart;
    XMLParserData *parserData;
    void *docBuf;
    size_t charsRead;

    if ( !INPUTFILE ) {
        fprintf( stderr, "Problem opening input file '%s'\n", fileName );
        return NULL;
    }

    if ( !p ) {
        fprintf( stderr, "Problem creating xml parser\n" );
        fclose( INPUTFILE );
        return NULL;
    }

    cart = CARTNode( -1, -1, NULL, 0, NULL );

    parserData = NewXMLParserData( cart, primaryFeatures, predictiveFeatures );
    XML_SetUserData( p, (void *)parserData );
    XML_SetCharacterDataHandler( p, XMLCharHandler );
    XML_SetElementHandler( p, XMLParsingStart, XMLParsingEnd );

    while ( !feof(INPUTFILE) ) {
        docBuf = XML_GetBuffer( p, XML_CHUNK_SIZE ); 
        if ( !docBuf ) {
            fprintf( stderr, "Problem getting the xml buffer\n" );
            fclose( INPUTFILE );
            return NULL;
        }
        charsRead = fread( docBuf, sizeof(char), XML_CHUNK_SIZE, INPUTFILE );
        if ( XML_ParseBuffer(p,(int)charsRead,0) == 0 ) {
            fprintf( stderr, "Problem parsing xml data\n" );
            fclose( INPUTFILE );
            return NULL;
        }
    }
    fclose( INPUTFILE );

    XML_ParserFree( p );

    *treeType = parserData->treeType;
    *key = parserData->key;

    FreeXMLParserData( parserData );
    free( parserData );

    return cart;
}

void LoadKnowledge( const char *fileName, CART **primaryCarts, CART **predictiveCarts, FeatureGroup *primaryFeatures, FeatureGroup *predictiveFeatures ) {
    FILE *INPUTFILE;
    char knowledgeFileName[1024];
    int treeType;
    unsigned char key;
    CART *tree;

    INPUTFILE = fopen( fileName, "r" );
    if ( !INPUTFILE ) {
        fprintf( stderr, "Problem opening file '%s'\n", fileName );
        return;
    }
    while ( !feof(INPUTFILE) ) {
        fscanf( INPUTFILE, "%s\n", knowledgeFileName );

        treeType = -1;
        key = 0;
        tree = BuildTree( knowledgeFileName, &treeType, &key, primaryFeatures, predictiveFeatures );
        if ( !tree ) continue;
        assert( key != 0 );
        if ( treeType == TREE_TYPE_PRIMARY ) {
            primaryCarts[key] = tree;
        }
        else if ( treeType == TREE_TYPE_PREDICTIVE ) {
            predictiveCarts[key] = tree;
        }
    }
    fclose( INPUTFILE );
}

NodeClass *LetterToClassLookup( FeatureGroup *featureGroup, CART *tree, const char *word, int focus, int multiple ) {
    CART *node = tree;
    CARTWord cartWord;
    char **classes;
    int i;

    assert( node );
    cartWord.word = word;
    cartWord.focus = focus;
    while ( !node->terminal ) {
        //printf("relIdx = %d, featureId = %s\n", node->splitRule.relativeIndex,
        //        node->splitRule.featureID);
        if ( Match(featureGroup,node,&cartWord) ) {
        //    printf("Got Match\n");
            node = node->leftCART;
        }
        else {
        //    printf("No Match\n");
            node = node->rightCART;
        }
    }
    /*
    if ( !multiple ) {
        classes = (char **) malloc( sizeof(char *) * 2 );
        classes[0] = strdup( node->classes[0].utf8Class );
        classes[1] = NULL;
        return classes;
    }
    classes = (char **) malloc( sizeof(char *) );
    for ( i = 0; node->classes[i].utf8Class; ++i ) {
        classes = (char **) realloc( classes, sizeof(char *) * (i+2) );
        classes[i] = strdup( node->classes[i].utf8Class );
    }
    classes[i] = NULL;
    return classes;
    */
    return node->classes;
}

void PrintCARTNode( CART *node ) {
    printf( "nodeID : %d\n", node->nodeID );
    //printf( "\tcontextLength : %d\n", node->contextLength );
    printf( "\tsplitrule : (%d,\"%s\")\n", node->splitRule.relativeIndex, node->splitRule.featureID );
    //printf( "\tclasses : (%s)\n", node->classes );
    printf( "\n" );
}

#if 0
int main( int argc, char *argv[] ) {
    int i, j;
    CART **primaryCarts, **predictiveCarts;
    char input[256];
    FILE *OUTPUTFILE;
    char **classes;
    FeatureGroup featureGroups[2];

    printf( "sizeof(CART) : %d\n", sizeof(CART) );

    primaryCarts = (CART **)malloc( sizeof(CART *) * 256 );
    predictiveCarts = (CART **)malloc( sizeof(CART *) * 256 );

    for ( i = 0; i < 256; ++i ) {
        primaryCarts[i] = NULL;
        predictiveCarts[i] = NULL;
    }

    for ( i = 0; i < 2; ++i ) {
        featureGroups[i].noOfFeatures = 0;
        featureGroups[i].features = (Feature *) malloc( sizeof(Feature) );
    }

    assert( argc >= 2 );
    LoadKnowledge( argv[1], primaryCarts, predictiveCarts, &(featureGroups[TREE_TYPE_PRIMARY]), &(featureGroups[TREE_TYPE_PREDICTIVE]) );

    OUTPUTFILE = fopen( "Output.txt", "a" );
    if ( !OUTPUTFILE ) {
        fprintf( stderr, "Error opening file Output.txt\n" );
        return -1;
    }

    //fprintf( OUTPUTFILE, "%c%c%c", 0xef, 0xbb, 0xbf );
    fflush( OUTPUTFILE );
    sprintf( input, "Bleeh" );
    while( 1 ) {
        printf( "$" );
        fflush( stdout );
        scanf( "%s", input );
        if ( strcmp(input,"end") ==  0 ) break;
        printf( "input(%d) : '%s'\n", strlen(input), input );

        for ( i = 0; i < (int)strlen(input); ++i ) {
            printf( "i : %d\t input : '%s'\n", i, input );
            if ( predictiveCarts[input[i]] ) { 
                classes = LetterToClassLookup( &(featureGroups[TREE_TYPE_PREDICTIVE]), predictiveCarts[input[i]], input, i, 0 );
                for ( j = 0; classes[j]; ++j ) {
                    printf( "Length of output : %d\n", strlen(classes[j]) );
                    fwrite( classes[j], sizeof(char), strlen(classes[j]), OUTPUTFILE);
                    free( classes[j] );
                }
                assert( j > 0 );
                free( classes );
            }
            else {
                fprintf( OUTPUTFILE, "%c", input[i] );
            }
        }
        fprintf( OUTPUTFILE, "\n" );
        fflush( OUTPUTFILE );
    }
    fclose( OUTPUTFILE );

    return 0;
}
#endif
