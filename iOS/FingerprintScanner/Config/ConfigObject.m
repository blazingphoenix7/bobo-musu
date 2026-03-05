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

#import "ConfigObject.h"
#import "MaskModelCreator.h"
#import "RingModelCreator.h"

@implementation ConfigObject

+ (ConfigObject*)fromDictionary:(NSDictionary*)dict {
    ConfigObject *obj = [ConfigObject new];
    obj.mask = dict[@"mask"];
    if (dict[@"mask_rectangle"]) {
        obj.rectangleMask = CGRectFromString(dict[@"mask_rectangle"]);
    }
    obj.transform = [Transform fromDictionary:dict[@"transform"]];
    return obj;
}

- (BaseModelCreator*)creator {
    if (self.mask) {
        return [[MaskModelCreator alloc] initWithConfig:self.config configObject:self];
    }
    
    return  [[RingModelCreator alloc] initWithConfig:self.config configObject:self];
}

@end
