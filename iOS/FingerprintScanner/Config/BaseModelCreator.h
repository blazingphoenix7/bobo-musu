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

struct ON_Mesh;
@class Export3dConfiguration, ConfigObject;
@interface BaseModelCreator : NSObject {
@public
    struct ON_Mesh *mesh;
}

@property (strong, nonatomic) Export3dConfiguration *config;
@property (strong, nonatomic) ConfigObject *configObject;
@property (strong, nonatomic) UIImage *image;
@property (assign, nonatomic) CGRect targetRect;

- (instancetype)initWithConfig:(Export3dConfiguration*)config
                  configObject:(ConfigObject*)configObject;

- (void)createModelFromImage:(UIImage*)image;
- (void)createVerticies;
- (void)createTriangles;
- (void)transform;

@end
