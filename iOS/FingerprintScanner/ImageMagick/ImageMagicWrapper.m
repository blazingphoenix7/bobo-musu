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

#import "ImageMagicWrapper.h"
#import "MagickWand.h"
#import "UIImage+Resize.h"

@interface ImageMagicWrapper ()

+ (UIImage *)prepareImage:(UIImage*)inputImage cropRatio:(float)cropRatio;
+ (UIImage *)processImage:(UIImage*)inputImage params:(NSArray*)params;

@end

@implementation ImageMagicWrapper

+ (UIImage *)prepareImage:(UIImage*)inputImage cropRatio:(float)cropRatio {
    CGFloat imageSize = 2000;
    inputImage = [inputImage resizedImageWithMaxEdge:imageSize];
    imageSize = MIN(inputImage.size.width, inputImage.size.height);
    CGPoint center = CGPointMake(inputImage.size.width/2, inputImage.size.height/2);
    CGFloat sizeCrop = imageSize*cropRatio;
    CGRect rcCrop = CGRectMake(center.x - sizeCrop/2, center.y - sizeCrop/2, sizeCrop, sizeCrop);
    return [inputImage croppedImage:rcCrop];
}
    
+ (UIImage *)processImage:(UIImage*)inputImage cropRatio:(float)cropRatio {
    inputImage = [ImageMagicWrapper prepareImage:inputImage cropRatio:cropRatio];

    NSArray *params = @[@"-fill", @"none", @"-fuzz", @"13%", @"-draw", @"matte 0,0 floodfill", @"-flop", @"-draw", @"matte 0,0 floodfill", @"-flop"];
    UIImage *imageWithoutBackground = [ImageMagicWrapper processImage:inputImage params:params];
    params = @[@"-fill", @"black", @"-floodfill", @"+10+10", @"black", @"-colorspace", @"gray", @"-lat", @"15x15-1%", @"-negate"];
    UIImage *imageRes = [ImageMagicWrapper processImage:imageWithoutBackground params:params];
    params = @[@"-fill", @"none", @"-fuzz", @"13%", @"-draw", @"matte 0,0 floodfill", @"-flop", @"-draw", @"matte 0,0 floodfill", @"-flop"];
    imageRes = [ImageMagicWrapper processImage:imageRes params:params];
    return imageRes;
}

+ (UIImage *)processImage:(UIImage*)inputImage params:(NSArray*)params {
    NSArray *paths = NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES);
    NSString *documentsPath = [paths objectAtIndex:0];
    NSString *filePath = [documentsPath stringByAppendingPathComponent:@"input.png"];
    NSData *pngData = UIImagePNGRepresentation(inputImage);
    [pngData writeToFile:filePath atomically:YES];
    
    char *input_image = strdup([filePath UTF8String]);
    
    NSString *filePathOutput = [documentsPath stringByAppendingPathComponent:@"output.png"];
    char *output_image = strdup([filePathOutput UTF8String]);
    char *args[20];
    args[0] = "convert";
    args[1] = input_image;
    int counter = 2;
    for (NSString *arg in params) {
        args[counter] = (char *)[arg UTF8String];
        counter ++;
    }
    args[counter] = output_image;
    
    MagickCoreGenesis(*args, MagickTrue);
    MagickWand *magickWand = NewMagickWand();
    NSData * dataObject = UIImageJPEGRepresentation([UIImage imageWithContentsOfFile:[NSString stringWithUTF8String:input_image]], 1.0f);
    MagickBooleanType status;
    status = MagickReadImageBlob(magickWand, [dataObject bytes], [dataObject length]);
    
    if (status == MagickFalse) {
        return nil;
    }
    
    int args_count = (int)params.count + 3;
    
    ImageInfo *image_info = AcquireImageInfo();
    ExceptionInfo *exception = AcquireExceptionInfo();
    
    status = ConvertImageCommand(image_info, args_count, args, NULL, exception);
    
    if (exception->severity != UndefinedException) {
        status = MagickTrue;
        CatchException(exception);
    }
    
    NSData *pngDataOutput = UIImageJPEGRepresentation([UIImage imageWithContentsOfFile:[NSString stringWithUTF8String:output_image]], 1.0f);
    status = MagickReadImageBlob(magickWand, [pngDataOutput bytes], [pngDataOutput length]);
    
    size_t my_size;
    unsigned char * my_image = MagickGetImageBlob(magickWand, &my_size);
    NSData * data = [[NSData alloc] initWithBytes:my_image length:my_size];
    free(my_image);
    magickWand = DestroyMagickWand(magickWand);
    MagickWandTerminus();
    UIImage *imageResult = [[UIImage alloc] initWithData:data];
    
    free(input_image);
    free(output_image);
    
    image_info = DestroyImageInfo(image_info);
    exception = DestroyExceptionInfo(exception);
    
    MagickCoreTerminus();
    
    return imageResult;
}

@end
