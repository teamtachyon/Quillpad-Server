#ifndef _Cart_H
#define _Cart_H

typedef char * FeatureID;
typedef struct {
    FeatureID featureID;
    char **featureTokens;
} Feature;

typedef struct {
    Feature *features;
    int noOfFeatures;
} FeatureGroup;

typedef struct {
    const char *word;
    int focus;
    char *classID;
    int count;
} CARTWord;

typedef struct {
    int relativeIndex;
    FeatureID featureID;
} SplitRule;

typedef struct {
    char *utf8Class;
    int frequency;
} NodeClass;

typedef struct CART {
    int nodeID;
//    int contextLength;
    char terminal;
    SplitRule splitRule;
    NodeClass *classes;
    struct CART *leftCART;
    struct CART *rightCART;
} CART;

CART *CARTNode( int nodeID, int contextLength, char *featureStr, char terminal, NodeClass *classes );
void SetNodeFeature( CART *node, FeatureGroup *featureGroup, const char *featureStr );
void SetNodeClasses( CART *node, const char *classesStr );

void AddBinaryNode( CART *root, CART *node );
int Match( FeatureGroup *featureGroup, CART *treeNode, const CARTWord *cartWord );

CART *BuildTree( const char *fileName, int *treeType, char *key, FeatureGroup *primaryFeatures, FeatureGroup *predictiveFeatures );
void LoadKnowledge( const char *fileName, CART **primaryCarts, CART **predictiveCarts, FeatureGroup *primaryFeatures, FeatureGroup *predictiveFeatures );

NodeClass *LetterToClassLookup( FeatureGroup *featureGroup, CART *tree, const char *word, int focus, int multiple );

void XMLElementRead( void *data, const char *element, const char *elementData );
void XMLAttrsRead( void *data, const char *element, const char **attr );

#endif
