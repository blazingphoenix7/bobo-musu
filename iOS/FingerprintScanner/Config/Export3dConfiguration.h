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

@interface Export3dConfiguration : NSObject

@property (assign, nonatomic) NSUInteger imageSize;
@property (assign, nonatomic) float extrusionHeight;
@property (strong, nonatomic) NSMutableArray *objects;

- (instancetype)initWithConfigPath:(NSString*)path;
- (instancetype)initWithFile:(NSString*)filename;

@end
