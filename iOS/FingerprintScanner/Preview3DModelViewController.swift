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

class RenderObject {
    var vbo = GLuint()
    var vao = GLuint()
    var isFingerprintMesh = false

    var vertices: [Vertex] = []
}

class Preview3DModelViewController: GLKViewController {
    var modelPath: String?

    private var renderObjects: [RenderObject] = []
    private var context: EAGLContext?

    private var effect = GLKBaseEffect()
    private var texture: GLKTextureInfo?

    private var rotation: Float = 0.0
    private var transformations: Transformations!

    var didDismiss: (() -> Void)?
    var didAddToCart: (() -> Void)?

    private var isAutoRotationMode = true

    override func viewDidLoad() {
        super.viewDidLoad()
        
        loadModel()
        setupGL()
        
        transformations = Transformations(depth: 6, scale: 0.12, translation: GLKVector2Make(0.0, 0.0), rotation: GLKVector3Make(0.0, 0.0, 0.0))
        transformations.scaleMax = 0.18
    }
    
    deinit {
        tearDownGL()
    }

    override func glkView(_ view: GLKView, drawIn rect: CGRect) {
        glClearColor(1, 1, 1, 1)
        glClear(GLbitfield(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT))

        glEnable(GLenum(GL_DEPTH_TEST))        // Enables Depth Testing
//        glDepthMask(GLboolean(GL_TRUE))
//        glDepthFunc(GLenum(GL_ALWAYS))         // The Type of Depth Test To do
//        glEnable(GLenum(GL_BLEND))
//        glBlendFunc(GLenum(GL_SRC_ALPHA), GLenum(GL_ONE_MINUS_SRC_ALPHA))
//        glBlendEquationOES(GLenum(GL_MIN_EXT))

//        glFrontFace(GLenum(GL_CCW))
//        glEnable(GLenum(GL_CULL_FACE))
//        glCullFace(GLenum(GL_FRONT))

        var shouldHideFingerprint = false
        if isAutoRotationMode {
            let rotationInt = Int(rotation) % 360
            shouldHideFingerprint = rotationInt >= 90 && rotationInt <= 270
        } else {
            let rotationX = abs(transformations.modelViewMatrix.rotationX)
            shouldHideFingerprint = rotationX >= 90
        }
        if shouldHideFingerprint {
            glEnable(GLenum(GL_CULL_FACE))
        } else {
            glDisable(GLenum(GL_CULL_FACE))
        }

        effect.prepareToDraw()

        for object in renderObjects {
            if object.isFingerprintMesh && shouldHideFingerprint {
                continue
            }

            glBindVertexArrayOES(object.vao)
            glDrawArrays(GLenum(GL_TRIANGLES), 0, GLsizei(object.vertices.count))
            glBindVertexArrayOES(0)
        }
    }

    private func loadModel() {
        renderObjects.removeAll()

        guard let modelPath = modelPath else { return }

        let model = Model3DManager()
        let arrayRenderContent = model.loadRenderContent(modelPath)
        arrayRenderContent?.forEach({ (renderContent) in
            let renderObject = RenderObject()
            renderObject.isFingerprintMesh = renderContent.isFingerprintMesh

            var index = 0
            renderContent.verticies.forEach({ (vert) in
                if let vert = vert as? CoordColor {
                    var nX: Float = 0.0, nY: Float = 0.0, nZ: Float = 0.0
                    if index < renderContent.normals.count,
                        let normal = renderContent.normals[index] as? Coord3D {

                        nX = normal.x
                        nY = normal.y
                        nZ = normal.z
                    }
                    var tX: Float = 0.0, tY: Float = 0.0
                    if index < renderContent.textureCoords.count,
                        let coord = renderContent.textureCoords[index] as? Coord2D {

                        tX = coord.x
                        tY = coord.y

                    }
                    let vertex = Vertex(x: vert.x, y: vert.y, z: vert.z,
                                        nX: nX, nY: nY, nZ: nZ,
                                        tX: tX, tY: tY,
                                        r: 0.83, g: 0.68, b: 0.22, a: 1)
//                        r: vert.r, g: vert.g, b: vert.b, a: vert.a)
                    renderObject.vertices.append(vertex)
                }
                index += 1
            })

            renderObjects.append(renderObject)
        })
    }
    
    private func setupGL() {
        context = EAGLContext(api: .openGLES3)
        EAGLContext.setCurrent(context)
        
        if let view = self.view as? GLKView, let context = context {
            view.context = context
            delegate = self
        }

//        do {
//            texture = try GLKTextureLoader.texture(withContentsOfFile: Bundle.main.path(forResource: "gold_tex", ofType: "png")!, options: [GLKTextureLoaderOriginBottomLeft:true, GLKTextureLoaderApplyPremultiplication:true])
//        }
//        catch let error as NSError {
//            print("could not load test texture \(error)")
//        }
//        effect.texture2d0.enabled = GLboolean(GL_TRUE)
//        effect.texture2d0.name = texture?.name ?? 0

        effect.lightModelAmbientColor = GLKVector4Make(0.5, 0.5, 0.5, 1)
        effect.colorMaterialEnabled = GLboolean(GL_TRUE)
        effect.material.shininess = 10.0
        effect.material.specularColor = GLKVector4Make(0.5, 0.5, 1, 1)

        effect.light0.enabled = GLboolean(GL_TRUE)
        effect.light0.position = GLKVector4Make(2, 4, 0, 0)

        renderObjects.forEach { (object) in
            setupRenderObject(object)
        }
    }

    private func setupRenderObject(_ object: RenderObject) {
        let vertexAttribColor = GLuint(GLKVertexAttrib.color.rawValue)
        let vertexAttribPosition = GLuint(GLKVertexAttrib.position.rawValue)
        let vertexSize = MemoryLayout<Vertex>.stride
        let colorOffset = MemoryLayout<GLfloat>.stride * 8
        let colorOffsetPointer = UnsafeRawPointer(bitPattern: colorOffset)
        let normalAttribPosition = GLuint(GLKVertexAttrib.normal.rawValue)
        let normalOffset = MemoryLayout<GLfloat>.stride * 3
        let normalOffsetPointer = UnsafeRawPointer(bitPattern: normalOffset)
        let textureCoordAttribPosition = GLuint(GLKVertexAttrib.texCoord0.rawValue)
        let textureCoordOffset = MemoryLayout<GLfloat>.stride * 6
        let textureCoordOffsetPointer = UnsafeRawPointer(bitPattern: textureCoordOffset)

        glGenVertexArraysOES(1, &object.vao)
        glBindVertexArrayOES(object.vao)

        glGenBuffers(1, &object.vbo)
        glBindBuffer(GLenum(GL_ARRAY_BUFFER), object.vbo)
        glBufferData(GLenum(GL_ARRAY_BUFFER),
                     object.vertices.size(),
                     object.vertices,
                     GLenum(GL_STATIC_DRAW))

        glEnableVertexAttribArray(vertexAttribPosition)
        glVertexAttribPointer(vertexAttribPosition,
                              3,
                              GLenum(GL_FLOAT),
                              GLboolean(UInt8(GL_FALSE)),
                              GLsizei(vertexSize),
                              nil)

        glEnableVertexAttribArray(vertexAttribColor)
        glVertexAttribPointer(vertexAttribColor,
                              4,
                              GLenum(GL_FLOAT),
                              GLboolean(UInt8(GL_FALSE)),
                              GLsizei(vertexSize),
                              colorOffsetPointer)

        glEnableVertexAttribArray(normalAttribPosition)
        glVertexAttribPointer(normalAttribPosition,
                              3,
                              GLenum(GL_FLOAT),
                              GLboolean(UInt8(GL_FALSE)),
                              GLsizei(vertexSize),
                              normalOffsetPointer)

        glEnableVertexAttribArray(textureCoordAttribPosition)
        glVertexAttribPointer(textureCoordAttribPosition,
                              2,
                              GLenum(GL_FLOAT),
                              GLboolean(UInt8(GL_FALSE)),
                              GLsizei(vertexSize),
                              textureCoordOffsetPointer)

        glBindVertexArrayOES(0)
        glBindBuffer(GLenum(GL_ARRAY_BUFFER), 0)
        glBindBuffer(GLenum(GL_ELEMENT_ARRAY_BUFFER), 0)
    }

    private func tearDownGL() {
        renderObjects.forEach { (object) in
            glDeleteBuffers(1, &object.vao)
            glDeleteBuffers(1, &object.vbo)
        }

        EAGLContext.setCurrent(nil)
        
        context = nil
    }
    
    @IBAction func close(_ sender: Any) {
        dismiss(animated: true, completion: didDismiss)
    }

    @IBAction func addToCart(_ sender: Any) {
        didAddToCart?()
    }

    @IBAction func pan(_ sender: UIPanGestureRecognizer) {
        if sender.numberOfTouches == 1 && (transformations.state == .new || transformations.state == .translation) {
            isAutoRotationMode = false
            let translation = sender.translation(in: sender.view)
            let x = translation.x/(sender.view?.frame.size.width ?? 1)
            let y = translation.y/(sender.view?.frame.size.height ?? 1)
            transformations.translate(GLKVector2Make(Float(x), Float(y)), multiplier: 5.0)
        }
        
        if sender.numberOfTouches == 2 && (transformations.state == .new || transformations.state == .rotation) {
            isAutoRotationMode = false
            let m = GLKMathDegreesToRadians(0.5)
            let rotation = sender.translation(in: sender.view)
            transformations.rotate(GLKVector3Make(Float(rotation.x), Float(rotation.y), 0.0), multiplier: m)
        }
    }

    @IBAction func pinch(_ sender: UIPinchGestureRecognizer) {
        if transformations.state == .new || transformations.state == .scale {
            isAutoRotationMode = false
            transformations.scale(Float(sender.scale))
        }
    }
    
    @IBAction func rotation(_ sender: UIRotationGestureRecognizer) {
        if transformations.state == .new || transformations.state == .rotation {
            isAutoRotationMode = false
            transformations.rotate(GLKVector3Make(0.0, 0.0, Float(sender.rotation)), multiplier: 1.0)
        }
    }
   
}

extension Preview3DModelViewController: GLKViewControllerDelegate {
    func glkViewControllerUpdate(_ controller: GLKViewController) {
        let aspect = fabsf(Float(view.bounds.size.width) / Float(view.bounds.size.height))
        let projectionMatrix = GLKMatrix4MakePerspective(GLKMathDegreesToRadians(65.0), aspect, 4.0, 10.0)
        effect.transform.projectionMatrix = projectionMatrix

        if isAutoRotationMode {
            var modelViewMatrix = GLKMatrix4MakeTranslation(0.0, 0.0, -6.0)
            rotation += 90 * Float(timeSinceLastUpdate)
            modelViewMatrix = GLKMatrix4Scale(modelViewMatrix, 0.12, 0.12, 0.12)
            modelViewMatrix = GLKMatrix4Rotate(modelViewMatrix, GLKMathDegreesToRadians(rotation), 0, 1, 0)
            effect.transform.modelviewMatrix = modelViewMatrix
        } else {
            effect.transform.modelviewMatrix = transformations.modelViewMatrix
        }
    }
}

extension Preview3DModelViewController {
    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent?) {
        transformations.start()
    }
}

extension Array {
    func size() -> Int {
        return MemoryLayout<Element>.stride * self.count
    }
}

extension GLKMatrix4 {
    public var rotationX: Float {
        return GLKMathRadiansToDegrees(atan2(m11, m22))
    }

    public var rotationY: Float {
        return GLKMathRadiansToDegrees(atan2(-m02, sqrt(m00*m00 + m01*m01)))
    }
}
