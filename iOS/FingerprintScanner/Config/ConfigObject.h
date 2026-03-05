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

#import <UIKit/UIKit.h>
#import "Transform.h"

@class Export3dConfiguration, BaseModelCreator;
@interface ConfigObject : NSObject

@property (strong, nonatomic) NSString *mask;
@property (assign, nonatomic) CGRect rectangleMask;
@property (strong, nonatomic) Transform *transform;
@property (strong, nonatomic) Export3dConfiguration *config;

+ (ConfigObject*)fromDictionary:(NSDictionary*)dict;
- (BaseModelCreator*)creator;

@end
