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

#import "BaseModelCreator.h"
#import "ConfigObject.h"
#include "opennurbs_public.h"
#import "Export3dConfiguration.h"

@interface BaseModelCreator ()

@end

@implementation BaseModelCreator

- (instancetype)initWithConfig:(Export3dConfiguration*)config
                  configObject:(ConfigObject*)configObject {
    self = [super init];
    if (self) {
        self.config = config;
        self.configObject = configObject;
   }
    return self;
}

- (void)createModelFromImage:(UIImage*)image {
    self.image = image;
    [self createVerticies];
    [self createTriangles];
    [self transform];
    
    if (!mesh->HasVertexNormals()) {
        mesh->ComputeVertexNormals();
    }
}

- (void)createVerticies {
    CGImageRef cgImage = self.image.CGImage;
    size_t width = CGImageGetWidth(cgImage);
    size_t height = CGImageGetHeight(cgImage);

    char *data = (char*)malloc(sizeof(char) * width * height * 4);
    CGColorSpaceRef colorSpace = CGColorSpaceCreateDeviceRGB();
    CGContextRef cgContext = CGBitmapContextCreate(data, width, height, 8, width * 4, colorSpace, kCGImageAlphaPremultipliedLast);
    CGContextSetBlendMode(cgContext, kCGBlendModeCopy);
    CGContextDrawImage(cgContext, CGRectMake(0.0f, 0.0f, width, height), cgImage);

    int index = 0;
    for (int x = CGRectGetMinX(self.targetRect); x < CGRectGetMaxX(self.targetRect); x++) {
        for (int y = CGRectGetMinY(self.targetRect); y < CGRectGetMaxY(self.targetRect); y++) {
            int pixelInfo = (self.image.size.width*y + x) * 4;
            UInt8 red = data[pixelInfo];
            mesh->SetVertex(index, ON_3dPoint(x - CGRectGetMinX(self.targetRect), y - CGRectGetMinY(self.targetRect), red > 100 ? 0 : self.config.extrusionHeight));
            index ++;
        }
    }
    
    free(data);
    CGContextRelease(cgContext);
    CGColorSpaceRelease(colorSpace);
}

- (void)createTriangles {
}

- (void)transform {
    ON_Xform transforScale;
    transforScale.Scale(self.configObject.transform.scaleX, self.configObject.transform.scaleY, self.configObject.transform.scaleZ);
    mesh->Transform(transforScale);
    
    ON_Xform transformTranslate;
    transformTranslate.Translation(self.configObject.transform.translateX, self.configObject.transform.translateY, self.configObject.transform.translateZ);
    mesh->Transform(transformTranslate);
}

@end
