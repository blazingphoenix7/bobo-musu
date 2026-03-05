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

#import "MaskModelCreator.h"
#import "ConfigObject.h"
#include "opennurbs_public.h"

@interface MaskModelCreator ()

@property (strong, nonatomic) UIImage *mask;

@end

struct MaskPixel {
    BOOL isIncluded;
    BOOL isBorder;
};

@implementation MaskModelCreator

- (instancetype)initWithConfig:(Export3dConfiguration*)config
                  configObject:(ConfigObject*)configObject {
    self = [super initWithConfig:config configObject:configObject];
    if (self) {
        // TODO: should be updated to use another paths
        NSArray *paths = NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES);
        NSString *documentsPath = [paths objectAtIndex:0];
       // NSString *maskPath = [documentsPath stringByAppendingPathComponent:self.configObject.mask];

        //self.mask = [UIImage imageWithContentsOfFile:maskPath];

        self.mask = [UIImage imageNamed:self.configObject.mask];
    }
    return self;
}

- (void)setImage:(UIImage *)image {
    [super setImage:image];

    CGSize szTarget = [self calcAspectFitRect:CGRectMake(0, 0, self.image.size.width, self.image.size.height) andSize:self.mask.size];
    self.targetRect = CGRectMake((self.image.size.width - szTarget.width)/2, (self.image.size.height - szTarget.height)/2, szTarget.width, szTarget.height);
}

- (void)createTriangles {
    if (!self.mask) {
        return;
    }

    int width = self.targetRect.size.width;
    int height = self.targetRect.size.height;
    int verticiesCount = width*height;

    CFDataRef pixelDataMask = CGDataProviderCopyData(CGImageGetDataProvider(self.mask.CGImage));
    const UInt8* dataMask = CFDataGetBytePtr(pixelDataMask);
    
    int counter = 0;
    for (int i = 0; i < verticiesCount; i++) {
        if (i > 0 && (i + 1) % height == 0) {
            continue;
        }
        
        if (i + height + 1 < verticiesCount && i + 1 < verticiesCount) {
            CGPoint pt1 = CGPointMake(i / height, i % height);
            CGPoint pt2 = CGPointMake((i + 1) / height, (i + 1) % height);
            CGPoint pt3 = CGPointMake((i + height) / height, (i + height) % height);
            CGPoint pt4 = CGPointMake((i + height + 1) / height, (i + height + 1) % height);
            MaskPixel maskPixel1 = [self maskPixel:pt1 maskData:dataMask sizeMask:self.mask.size];
            MaskPixel maskPixel2 = [self maskPixel:pt2 maskData:dataMask sizeMask:self.mask.size];
            MaskPixel maskPixel3 = [self maskPixel:pt3 maskData:dataMask sizeMask:self.mask.size];
            MaskPixel maskPixel4 = [self maskPixel:pt4 maskData:dataMask sizeMask:self.mask.size];
            if (maskPixel1.isIncluded && maskPixel2.isIncluded && maskPixel4.isIncluded) {
                if (maskPixel1.isBorder) {
                    [self setVertexBorder:i];
                }
                if (maskPixel2.isBorder) {
                    [self setVertexBorder:i + 1];
                }
                if (maskPixel4.isBorder) {
                    [self setVertexBorder:i + height + 1];
                }
                mesh->SetTriangle(counter++, i, i + 1, i + height + 1);
            }
            if (maskPixel1.isIncluded && maskPixel3.isIncluded && maskPixel4.isIncluded) {
                if (maskPixel1.isBorder) {
                    [self setVertexBorder:i];
                }
                if (maskPixel3.isBorder) {
                    [self setVertexBorder:i + height];
                }
                if (maskPixel4.isBorder) {
                    [self setVertexBorder:i + height + 1];
                }

                mesh->SetTriangle(counter++, i, i + height + 1, i + height);
            }
        }
    }

    CFRelease(pixelDataMask);
}

- (CGSize)calcAspectFitRect:(CGRect)rcOuter andSize:(CGSize)szSize {
    CGSize szRet = CGSizeMake(rcOuter.size.width, MAX(1, rcOuter.size.height));
    double dFactor = szRet.width / (double)szRet.height;
    if (szSize.height * dFactor > szSize.width) {
        szRet.width = szRet.height * szSize.width / MAX( 1, szSize.height );
    } else {
        szRet.height = szRet.width * szSize.height / MAX( 1, szSize.width );
    }
    
    return szRet;
}

- (MaskPixel)maskPixel:(CGPoint)pt maskData:(const UInt8*)maskData sizeMask:(CGSize)sizeMask {
    int maskX = pt.x;
    int maskY = pt.y;
    
    int pixelInfo = (sizeMask.width*maskY + maskX) * 4;
    UInt8 red = maskData[pixelInfo];
    MaskPixel maskPixel;
    maskPixel.isIncluded = (red <= 127);
    maskPixel.isBorder = (maskPixel.isIncluded && red > 0);
    return maskPixel;
}

- (void)setVertexBorder:(int)vertexIndex {
    ON_COMPONENT_INDEX index(ON_COMPONENT_INDEX::mesh_vertex, vertexIndex);
    ON_MeshComponentRef vertex = mesh->MeshComponentRef(index);
    ON_3dPoint point = vertex.VertexPoint();
    point.z = 0;
    mesh->SetVertex(vertexIndex, point);
}

@end
