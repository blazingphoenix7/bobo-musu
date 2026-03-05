/*************************************************************************
 *
 * BOBO AND MUSU CONFIDENTIAL
 * __________________
 *
 *  2017 Bobo and Musu
 *  All Rights Reserved.
 *
 * NOTICE:  All information contained herein is, and remains
 * the property of Bobo and Musu and its suppliers,
 * if any.  The intellectual and technical concepts contained
 * herein are proprietary to Bobo and Musu
 * and its suppliers and may be covered by U.S. and Foreign Patents,
 * patents in process, and are protected by trade secret or copyright law.
 * Dissemination of this information or reproduction of this material
 * is strictly forbidden unless prior written permission is obtained
 * from Bobo and Musu.
 */

#import "RenderContent.h"

@implementation RenderContent

- (void)addVertex:(CoordColor*)vertex {
    [self.verticies addObject:vertex];
}

- (void)addNormal:(Coord3D*)normal {
    [self.normals addObject:normal];
}

- (void)addTextureCoord:(Coord2D*)coord {
    [self.textureCoords addObject:coord];
}

- (NSMutableArray*)verticies {
    if (!_verticies) {
        _verticies = [NSMutableArray new];
    }
    
    return _verticies;
}

- (NSMutableArray*)normals {
    if (!_normals) {
        _normals = [NSMutableArray new];
    }
    
    return _normals;
}

- (NSMutableArray*)textureCoords {
    if (!_textureCoords) {
        _textureCoords = [NSMutableArray new];
    }
    
    return _textureCoords;
}

@end
