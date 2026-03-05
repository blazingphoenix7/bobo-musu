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

#import "Transform.h"

@implementation Transform

+ (Transform*)fromDictionary:(NSDictionary*)dict {
    Transform *transform = [Transform new];
    transform.scaleX = [dict[@"scaleX"] doubleValue];
    transform.scaleY = [dict[@"scaleY"] doubleValue];
    transform.scaleZ = [dict[@"scaleZ"] doubleValue];
    transform.translateX = [dict[@"translateX"] doubleValue];
    transform.translateY = [dict[@"translateY"] doubleValue];
    transform.translateZ = [dict[@"translateZ"] doubleValue];
    transform.file = dict[@"file"];
    return transform;
}

@end
