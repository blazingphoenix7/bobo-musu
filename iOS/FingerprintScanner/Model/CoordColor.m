//
//  CoordColor.m
//  FingerprintScanner
//
//  Created by Denis Trubenkov on 12/26/18.
//  Copyright © 2018 FSStudio. All rights reserved.
//

#import "CoordColor.h"

@implementation CoordColor

- (instancetype)initWithX:(float)x y:(float)y z:(float)z color:(UIColor*)color {
    self = [super initWithX:x y:y z:z];
    if (self) {
        CGFloat r, g, b, a;
        [color getRed:&r green:&g blue:&b alpha:&a];
        self.r = r;
        self.g = g;
        self.b = b;
        self.a = a;
    }
    
    return self;
}

@end
