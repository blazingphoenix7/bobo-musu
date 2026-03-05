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


#import "Model3DManager.h"
#include "opennurbs_public.h"
#import "UIImage+Resize.h"
#import "Export3dConfiguration.h"
#import "ConfigObject.h"
#import "BaseModelCreator.h"

static Model3DManager *_shared = nil;
static dispatch_once_t once_token = 0;

@interface Model3DManager ()

@end

@implementation Model3DManager

+ (instancetype)shared {
    dispatch_once(&once_token, ^{
        _shared = [[Model3DManager alloc] init];
    });
    return _shared;
}

- (instancetype)init {
    self = [super init];
    if (self) {
    }
    return self;
}

ON_3dmObjectAttributes* Internal_CreateManagedAttributes(
                                                         int layer_index,
                                                         const wchar_t* name
                                                         )
{
    ON_3dmObjectAttributes* attributes = new ON_3dmObjectAttributes();
    attributes->m_layer_index = layer_index;
    attributes->m_name = name;
    return attributes;
}

- (BOOL)createModelFromFingerImage:(UIImage*)image
                      templatePath:(NSString*)templatePath
                        configPath:(NSString*)configPath
                        outputFile:(NSString*)filePath {
    ON_TextLog error_log;
    ONX_Model model;
    if (!model.Read(templatePath.UTF8String, &error_log)) {
        return NO;
    }

    Export3dConfiguration *config = [[Export3dConfiguration alloc] initWithConfigPath:configPath];

    CGFloat cropSize = MIN(image.size.width, image.size.height);
    CGRect cropRect = CGRectMake(image.size.width - cropSize, image.size.height - cropSize, cropSize, cropSize);
    image = [image croppedImage:cropRect];
    image = [image resizedImageWithMaxEdge:config.imageSize];

    for (ConfigObject *obj in config.objects) {
        BaseModelCreator *modelCreator = [obj creator];
        if (!modelCreator) {
            return NO;
        }

        ON_Mesh *mesh = new ON_Mesh(1, image.size.width*image.size.height, true, false);
        modelCreator->mesh = mesh;
        [modelCreator createModelFromImage:image];
        model.AddModelGeometryComponentForExperts(false, mesh, false, nullptr, true);
    }

    model.Write(filePath.UTF8String, 50, &error_log);

    NSLog(@"OK %@", filePath);
    return YES;
}

- (BOOL)createModelFromFingerImage:(UIImage*)image modelName:(NSString*)modelName outputFile:(NSString*)filePath {
#if TARGET_IPHONE_SIMULATOR
    image = [UIImage imageNamed:@"sample.jpg"];
#endif
    
    ON_TextLog error_log;
    ONX_Model model;
    NSString *pathTemplate = [[NSBundle mainBundle] pathForResource:modelName ofType:@"3dm"];
    if (!model.Read(pathTemplate.UTF8String, &error_log)) {
        return NO;
    }
    
    Export3dConfiguration *config = [[Export3dConfiguration alloc] initWithFile:modelName];
    
    CGFloat cropSize = MIN(image.size.width, image.size.height);
    CGRect cropRect = CGRectMake(image.size.width - cropSize, image.size.height - cropSize, cropSize, cropSize);
    image = [image croppedImage:cropRect];
    image = [image resizedImageWithMaxEdge:config.imageSize];

    for (ConfigObject *obj in config.objects) {
        BaseModelCreator *modelCreator = [obj creator];
        if (!modelCreator) {
            return NO;
        }
        
        ON_Mesh *mesh = new ON_Mesh(1, image.size.width*image.size.height, true, false);
        modelCreator->mesh = mesh;
        [modelCreator createModelFromImage:image];
        model.AddModelGeometryComponentForExperts(false, mesh, false, nullptr, true);
    }
    
    model.Write(filePath.UTF8String, 50, &error_log);
    
    NSLog(@"OK %@", filePath);
    return YES;
}

- (NSArray<RenderContent*>*)loadRenderContent:(NSString*)filename {
    ON_TextLog error_log;
    ONX_Model model;
    if (!model.Read(filename.UTF8String, &error_log)) {
        return @[];
    }

    NSMutableArray *result = [NSMutableArray new];

    ONX_ModelComponentIterator it(model, ON_ModelComponent::Type::ModelGeometry);
    const ON_ModelComponent* model_component = nullptr;
    for (model_component = it.FirstComponent(); nullptr != model_component; model_component = it.NextComponent())
    {
        const ON_ModelGeometryComponent* model_geometry = ON_ModelGeometryComponent::Cast(model_component);
        if (nullptr != model_geometry)
        {
            const ON_Mesh* mesh = ON_Mesh::Cast(model_geometry->Geometry(nullptr));
            if (nullptr != mesh)
            {
                UIColor *randomRGBColor = [[UIColor alloc] initWithRed:arc4random()%256/256.0
                                                                 green:arc4random()%256/256.0
                                                                  blue:arc4random()%256/256.0
                                                                 alpha:1.0];
                RenderContent *content = [RenderContent new];
                content.isFingerprintMesh = YES;
                [self loadMesh:mesh renderContent:content color:randomRGBColor];
                [result addObject:content];
                continue;
            }
            
            const ON_Brep* brep = ON_Brep::Cast(model_geometry->Geometry(nullptr));
            if (nullptr != brep)
            {
                RenderContent *content = [RenderContent new];
                const int face_count = brep->m_F.Count();
                int face_index;
                for ( face_index = 0; face_index < face_count; face_index++ ) {
                    const ON_BrepFace& face = brep->m_F[face_index];
                    const ON_Mesh* mesh = face.Mesh(ON::render_mesh);
                    if (nullptr != mesh) {
                        UIColor *randomRGBColor = [[UIColor alloc] initWithRed:arc4random()%256/256.0
                                                                         green:arc4random()%256/256.0
                                                                          blue:arc4random()%256/256.0
                                                                         alpha:1.0];
                         [self loadMesh:mesh renderContent:content color:randomRGBColor];
                    } else {
//                        [self loadBrepFaceWithoutMesh:face renderContent:content];
                    }
                }

                [result addObject:content];
                continue;
            }
            
            const ON_Extrusion* extrusion = ON_Extrusion::Cast(model_geometry->Geometry(nullptr));
            if (nullptr != extrusion)
            {
                const ON_Mesh* mesh = extrusion->m_mesh_cache.Mesh(ON::render_mesh);
                if (nullptr != mesh)
                {
                    UIColor *randomRGBColor = [[UIColor alloc] initWithRed:arc4random()%256/256.0
                                                                     green:arc4random()%256/256.0
                                                                      blue:arc4random()%256/256.0
                                                                     alpha:1.0];
                    RenderContent *content = [RenderContent new];
                    [self loadMesh:mesh renderContent:content color:randomRGBColor];
                    [result addObject:content];
                }
                continue;
            }
        }
    }


    return result;
}

- (void)loadMesh:(const ON_Mesh*)mesh renderContent:(RenderContent*)renderContent color:(UIColor*)color {
    int i0, i1, i2, j0, j1, j2;
    int fi;
    
    ON_3fPoint v[4];
    ON_3fVector n[4];
    ON_2fPoint t[4];
    
    const int face_count = mesh->FaceCount();
    const bool bHasNormals = mesh->HasVertexNormals();
    const bool bHasTCoords = mesh->HasTextureCoordinates();
    
    for ( fi = 0; fi < face_count; fi++ ) {
        const ON_MeshFace& f = mesh->m_F[fi];
        
        v[0] = mesh->m_V[f.vi[0]];
        v[1] = mesh->m_V[f.vi[1]];
        v[2] = mesh->m_V[f.vi[2]];
        
        if ( bHasNormals ) {
            n[0] = mesh->m_N[f.vi[0]];
            n[1] = mesh->m_N[f.vi[1]];
            n[2] = mesh->m_N[f.vi[2]];
        }
        
        if ( bHasTCoords ) {
            t[0] = mesh->m_T[f.vi[0]];
            t[1] = mesh->m_T[f.vi[1]];
            t[2] = mesh->m_T[f.vi[2]];
        }
        
        if ( f.IsQuad() ) {
            // quadrangle - render as two triangles
            v[3] = mesh->m_V[f.vi[3]];
            if ( bHasNormals )
                n[3] = mesh->m_N[f.vi[3]];
            if ( bHasTCoords )
                t[3] = mesh->m_T[f.vi[3]];
            if ( v[0].DistanceTo(v[2]) <= v[1].DistanceTo(v[3]) ) {
                i0 = 0; i1 = 1; i2 = 2;
                j0 = 0; j1 = 2; j2 = 3;
            }
            else {
                i0 = 1; i1 = 2; i2 = 3;
                j0 = 1; j1 = 3; j2 = 0;
            }
        }
        else {
            // single triangle
            i0 = 0; i1 = 1; i2 = 2;
            j0 = j1 = j2 = 0;
        }
        
        // first triangle
        if (bHasNormals) {
            [renderContent addNormal:[[Coord3D alloc] initWithX:n[i0].x y:n[i0].y z:n[i0].z]];
        }
        if ( bHasTCoords ) {
            [renderContent addTextureCoord:[[Coord2D alloc] initWithX:t[i0].x y:t[i0].y]];
        }
        [renderContent addVertex:[[CoordColor alloc] initWithX:v[i0].x y:v[i0].y z:v[i0].z color:color]];
        
        if (bHasNormals) {
            [renderContent addNormal:[[Coord3D alloc] initWithX:n[i1].x y:n[i1].y z:n[i1].z]];
        }
        if ( bHasTCoords ) {
            [renderContent addTextureCoord:[[Coord2D alloc] initWithX:t[i1].x y:t[i1].y]];
        }
        [renderContent addVertex:[[CoordColor alloc] initWithX:v[i1].x y:v[i1].y z:v[i1].z color:color]];

        if (bHasNormals) {
            [renderContent addNormal:[[Coord3D alloc] initWithX:n[i2].x y:n[i2].y z:n[i2].z]];
        }
        if ( bHasTCoords ) {
            [renderContent addTextureCoord:[[Coord2D alloc] initWithX:t[i2].x y:t[i2].y]];
        }
        [renderContent addVertex:[[CoordColor alloc] initWithX:v[i2].x y:v[i2].y z:v[i2].z color:color]];
        
        if ( j0 != j1 ) {
            // if we have a quad, second triangle
            if (bHasNormals) {
                [renderContent addNormal:[[Coord3D alloc] initWithX:n[j0].x y:n[j0].y z:n[j0].z]];
            }
            if ( bHasTCoords ) {
                [renderContent addTextureCoord:[[Coord2D alloc] initWithX:t[j0].x y:t[j0].y]];
            }
            [renderContent addVertex:[[CoordColor alloc] initWithX:v[j0].x y:v[j0].y z:v[j0].z color:color]];

            if (bHasNormals) {
                [renderContent addNormal:[[Coord3D alloc] initWithX:n[j1].x y:n[j1].y z:n[j1].z]];
            }
            if ( bHasTCoords ) {
                [renderContent addTextureCoord:[[Coord2D alloc] initWithX:t[j1].x y:t[j1].y]];
            }
            [renderContent addVertex:[[CoordColor alloc] initWithX:v[j1].x y:v[j1].y z:v[j1].z color:color]];

            if (bHasNormals) {
                [renderContent addNormal:[[Coord3D alloc] initWithX:n[j2].x y:n[j2].y z:n[j2].z]];
            }
            if ( bHasTCoords ) {
                [renderContent addTextureCoord:[[Coord2D alloc] initWithX:t[j2].x y:t[j2].y]];
            }
            [renderContent addVertex:[[CoordColor alloc] initWithX:v[j2].x y:v[j2].y z:v[j2].z color:color]];
        }
        
    }
}

- (void)loadBrepFaceWithoutMesh:(const ON_BrepFace&)face renderContent:(RenderContent*)renderContent {
    const ON_Brep* brep = face.Brep();
    if ( !brep )
        return;
    
    bool bSkipTrims = false;
    double knot_scale[2][2] = {{0.0,1.0},{0.0,1.0}};
    
    // untrimmed surface
    {
        ON_NurbsSurface tmp_nurbssrf;
        const ON_Surface* srf = brep->m_S[face.m_si];
        const ON_NurbsSurface* nurbs_srf = ON_NurbsSurface::Cast(srf);
        if ( !nurbs_srf )
        {
            // attempt to get NURBS form of this surface
            if ( srf->GetNurbForm( tmp_nurbssrf ) )
                nurbs_srf = &tmp_nurbssrf;
        }
        if ( !nurbs_srf )
            return;
        
        if ( bSkipTrims || brep->FaceIsSurface( face.m_face_index ) ) {
            return; // face is trivially trimmed
        }
        
        const ON_NurbsSurface& s = *nurbs_srf;
        int bPermitKnotScaling = true;
        double* knot_scale0 = knot_scale[0];
        double* knot_scale1 = knot_scale[1];

        int i, j, k;
        
        // The "bPermitScaling" parameters to the ON_GL() call that
        // fills in the knot vectors is set to false because any
        // rescaling that is applied to a surface domain must also
        // be applied to parameter space trimming curve geometry.
        
        // GL "s" knots
        GLint sknot_count = s.KnotCount(0) + 2;
        GLfloat* sknot = (GLfloat*)onmalloc( sknot_count*sizeof(*sknot) );
//        ON_GL( s.Order(0), s.CVCount(0), s.Knot(0), sknot,
//              bPermitKnotScaling, knot_scale0 );
        
        // GL "t" knots
        GLint tknot_count = s.KnotCount(1) + 2;
        GLfloat* tknot = (GLfloat*)onmalloc( tknot_count*sizeof(*tknot) );
//        ON_GL( s.Order(1), s.CVCount(1), s.Knot(1), tknot,
//              bPermitKnotScaling, knot_scale1 );
        
        // control vertices
        const int cv_size= s.CVSize();
        const int cv_count[2] = {s.CVCount(0), s.CVCount(1)};
        GLint s_stride = cv_size*cv_count[1];
        GLint t_stride = cv_size;
        GLfloat* ctlarray = (GLfloat*)onmalloc( s_stride*cv_count[0]*sizeof(*ctlarray) );
        for ( i = 0; i < cv_count[0]; i++ ) {
            for ( j = 0; j < cv_count[1]; j++ ) {
                const double*  cv = s.CV(i,j);
                GLfloat* gl_cv = ctlarray + s_stride*i + t_stride*j;
                for ( k = 0; k < cv_size; k++ ) {
                    gl_cv[k] = (GLfloat)cv[k];
                }
            }
        }
        
        GLint sorder = s.Order(0);
        GLint torder = s.Order(1);
        
//        gluNurbsSurface (
//                         nobj,
//                         sknot_count,
//                         sknot,
//                         tknot_count,
//                         tknot,
//                         s_stride,
//                         t_stride,
//                         ctlarray,
//                         sorder,
//                         torder,
//                         type
//                         );
        
        onfree( ctlarray );
        onfree( tknot );
        onfree( sknot );
    }
    
}

@end
