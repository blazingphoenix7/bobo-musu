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

#import "RingModelCreator.h"
#import "ConfigObject.h"
#include "opennurbs_public.h"
#import "Export3dConfiguration.h"

@interface RingModelCreator ()

@property (assign, nonatomic) int pointsInCircle;
@property (assign, nonatomic) int verticiesCount;

@end

@implementation RingModelCreator

- (instancetype)initWithConfig:(Export3dConfiguration*)config
                  configObject:(ConfigObject*)configObject {
    self = [super initWithConfig:config configObject:configObject];
    if (self) {
        self.targetRect = configObject.rectangleMask;
    }
    return self;
}

- (void)createVerticies {
    CFDataRef pixelData = CGDataProviderCopyData(CGImageGetDataProvider(self.image.CGImage));
    const UInt8* data = CFDataGetBytePtr(pixelData);
    
    self.verticiesCount = 0;
    for (int i = CGRectGetMinX(self.targetRect); i <= CGRectGetMaxX(self.targetRect); i++) {
        self.pointsInCircle = 0;
        float y = i - CGRectGetMinX(self.targetRect);
        int radius = [self radiusForCoord:y];
        for (float theta = 0; theta <= 2*M_PI; theta += 0.01) {
            float z = radius * cos(theta);
            float x = radius * sin(theta);
            
            int imageX = i;
            int imageY = round(radius*theta) + CGRectGetMinY(self.targetRect);
            if (imageY > CGRectGetMaxY(self.targetRect)) {
                imageY = 2*CGRectGetMaxY(self.targetRect) - imageY;
            }
            int pixelInfo = (self.image.size.width*imageY + imageX) * 4;
            UInt8 red = data[pixelInfo];
            if (y > 0 && y < self.targetRect.size.width && red < 100) {
                z = (radius + self.config.extrusionHeight) * cos(theta);
                x = (radius + self.config.extrusionHeight) * sin(theta);
            }

            mesh->SetVertex(self.verticiesCount, ON_3dPoint(x, y, z));
            self.verticiesCount ++;
            self.pointsInCircle ++;
        }
    }
    
    CFRelease(pixelData);
}

- (void)createTriangles {
    int counter = 0;
    for (int i = 0; i < self.verticiesCount; i++) {
        if (i + self.pointsInCircle + 1 < self.verticiesCount && i + 1 < self.verticiesCount) {
            mesh->SetTriangle(counter++, i, i + 1, i + self.pointsInCircle + 1);
            mesh->SetTriangle(counter++, i, i + self.pointsInCircle + 1, i + self.pointsInCircle);
        }
    }
}

- (float)radiusForCoord:(int)coord {
    float radius = (self.targetRect.size.height * 2)/(2*M_PI);
    
//    int padding = 20;
    int offset = 0;
//    if (coord < padding /*|| coord > CGRectGetMaxX(self.targetRect) - padding*/) {
//        int x = 20 - coord;
//    }
    
    return radius - offset;
}

@end
