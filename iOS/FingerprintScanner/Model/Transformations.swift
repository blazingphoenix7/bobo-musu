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

import GLKit

enum TransformationState {
    case new
    case scale
    case translation
    case rotation
}

class Transformations: NSObject {
    var state: TransformationState?
    
    fileprivate var right: GLKVector3!
    fileprivate var up: GLKVector3!
    fileprivate var front: GLKVector3!

    // Depth
    fileprivate var depth: Float!
    
    // Scale
    fileprivate var scaleStart: Float!
    fileprivate var scaleEnd: Float!
    
    // Translation
    fileprivate var translationStart: GLKVector2!
    fileprivate var translationEnd: GLKVector2!
    
    // Rotation
    fileprivate var rotationStart: GLKVector3!
    fileprivate var rotationEnd: GLKQuaternion!

    public var scaleMax: Float?

    var modelViewMatrix: GLKMatrix4 {
        var modelViewMatrix = GLKMatrix4Identity
        let quaternionMatrix = GLKMatrix4MakeWithQuaternion(rotationEnd)
        modelViewMatrix = GLKMatrix4Translate(modelViewMatrix, translationEnd.x, translationEnd.y, -depth)
        modelViewMatrix = GLKMatrix4Multiply(modelViewMatrix, quaternionMatrix)
        modelViewMatrix = GLKMatrix4Scale(modelViewMatrix, scaleEnd, scaleEnd, scaleEnd)
        return modelViewMatrix
    }
    
    init(depth: Float, scale: Float, translation: GLKVector2, rotation: GLKVector3) {
        right = GLKVector3Make(1.0, 0.0, 0.0)
        up = GLKVector3Make(0.0, 1.0, 0.0)
        front = GLKVector3Make(0.0, 0.0, 1.0)
        
        self.depth = depth
        scaleEnd = scale
        translationEnd = translation

        var r = rotation
        r.x = GLKMathDegreesToRadians(r.x)
        r.y = GLKMathDegreesToRadians(r.y)
        r.z = GLKMathDegreesToRadians(r.z)

        rotationEnd = GLKQuaternionIdentity
        rotationEnd = GLKQuaternionMultiply(GLKQuaternionMakeWithAngleAndVector3Axis(-r.x, right), rotationEnd)
        rotationEnd = GLKQuaternionMultiply(GLKQuaternionMakeWithAngleAndVector3Axis(-r.y, up), rotationEnd);
        rotationEnd = GLKQuaternionMultiply(GLKQuaternionMakeWithAngleAndVector3Axis(-r.z, front), rotationEnd);
    }
    
    func start() {
        state = .new
        scaleStart = scaleEnd
        translationStart = GLKVector2Make(0.0, 0.0)
        rotationStart = GLKVector3Make(0.0, 0.0, 0.0)
    }
    
    func scale(_ s: Float) {
        state = .scale
        if let scaleMax = scaleMax {
            scaleEnd = min(s * scaleStart, scaleMax)
        } else {
            scaleEnd = s * scaleStart
        }
    }
    
    func translate(_ t: GLKVector2, multiplier: Float) {
        state = .translation
        
        var tr = t
        tr = GLKVector2MultiplyScalar(tr, multiplier)
        
        let dx = translationEnd.x + (tr.x - translationStart.x)
        let dy = translationEnd.y - (tr.y - translationStart.y)
        
        translationEnd = GLKVector2Make(dx, dy)
        translationStart = GLKVector2Make(tr.x, tr.y)
    }
    
    func rotate(_ r: GLKVector3, multiplier: Float) {
        state = .rotation
        
        let dx = r.x - rotationStart.x
        let dy = r.y - rotationStart.y
        let dz = r.z - rotationStart.z
        
        rotationStart = GLKVector3Make(r.x, r.y, r.z)
        rotationEnd = GLKQuaternionMultiply(GLKQuaternionMakeWithAngleAndVector3Axis(dx*multiplier, up), rotationEnd)
        rotationEnd = GLKQuaternionMultiply(GLKQuaternionMakeWithAngleAndVector3Axis(dy*multiplier, right), rotationEnd)
        rotationEnd = GLKQuaternionMultiply(GLKQuaternionMakeWithAngleAndVector3Axis(-dz, front), rotationEnd)
    }
}
