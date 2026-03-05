//
//  CoordColor.h
//  FingerprintScanner
//
//  Created by Denis Trubenkov on 12/26/18.
//  Copyright © 2018 FSStudio. All rights reserved.
//

#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#import "Coord3D.h"

NS_ASSUME_NONNULL_BEGIN

@interface CoordColor : Coord3D

@property (assign, nonatomic) float r, g, b, a;

- (instancetype)initWithX:(float)x y:(float)y z:(float)z color:(UIColor*)color;

@end

NS_ASSUME_NONNULL_END
