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

#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#import "CoordColor.h"
#import "Coord2D.h"

@interface RenderContent : NSObject

@property (strong, nonatomic) NSMutableArray *verticies;
@property (strong, nonatomic) NSMutableArray *normals;
@property (strong, nonatomic) NSMutableArray *textureCoords;
@property (assign, nonatomic) BOOL isFingerprintMesh;

- (void)addVertex:(CoordColor*)vertex;
- (void)addNormal:(Coord3D*)normal;
- (void)addTextureCoord:(Coord2D*)coord;

@end
