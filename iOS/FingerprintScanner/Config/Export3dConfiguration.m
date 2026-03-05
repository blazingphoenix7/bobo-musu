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

#import "Export3dConfiguration.h"
#import "ConfigObject.h"

@implementation Export3dConfiguration

- (instancetype)initWithConfigPath:(NSString*)path {
    self = [super init];
    if (self) {
        NSDictionary *config = [NSDictionary dictionaryWithContentsOfFile:path];

        self.imageSize = [config[@"imageSize"] integerValue];
        self.extrusionHeight = [config[@"extrusionHeight"] floatValue];

        self.objects = [NSMutableArray new];
        for (NSDictionary *dictObj in config[@"objects"]) {
            ConfigObject *obj = [ConfigObject fromDictionary:dictObj];
            obj.config = self;
            [self.objects addObject:obj];
        }
    }
    return self;
}

- (instancetype)initWithFile:(NSString*)filename {
    NSString *configPath = [[NSBundle mainBundle] pathForResource:filename ofType:@"plist"];
    return [self initWithConfigPath:configPath];
}

@end
