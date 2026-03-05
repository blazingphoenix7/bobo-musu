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

import UIKit
import Alamofire

class NetworkManager {
    internal struct API {
        //static let host = "http://ec2-13-58-173-199.us-east-2.compute.amazonaws.com"
        static let host = "http://ec2-18-223-107-117.us-east-2.compute.amazonaws.com"
        static let baseURL = "\(host)/api/"
        static let uploadPath = "\(baseURL)/uploadprint"
        static let addToCartPath = "\(baseURL)/addtocart"
        static let downloadModelTemplatePath = "\(baseURL)/downloadModelTemplate"
   }

    static var shared = NetworkManager(baseURL: API.baseURL)


    let baseURL: String!

    private init(baseURL: String) {
        self.baseURL = baseURL
    }

    public func uploadFingerprint(image: UIImage,
                                  userName: String,
                                  success: @escaping () -> Void,
                                  failure: @escaping (String) -> Void) {

        guard let customerId = Session.shared.customerId,
            let imageData = UIImageJPEGRepresentation(image, 1) else {
                failure("Invalid data")
                return
        }

        Alamofire.upload(multipartFormData: { (form) in
            form.append(imageData, withName: "files[0]", fileName: "fingerprint.jpg", mimeType: "image/jpeg")
            form.append(userName.data(using: .utf8)!, withName: "name")
            form.append(customerId.data(using: .utf8)!, withName: "customerid")
        }, to: NetworkManager.API.uploadPath, encodingCompletion: { result in
            switch result {
            case .success(let upload, _, _):
                upload.responseJSON { response in
                    switch response.result {
                    case .success(let JSON):
                        print("JSON: \(JSON)")
                        success()
                    case .failure(let error):
                        print(error)
                        failure(error.localizedDescription)
                    }
                }
            case .failure(let encodingError):
                failure(encodingError.localizedDescription)
            }
        })
    }

    public func addToCart(modelFilePath: String,
                          productId: String,
                          printId: String,
                          success: @escaping () -> Void,
                          failure: @escaping (String) -> Void) {


        guard let customerId = Session.shared.customerId,
                let modelData = try? Data(contentsOf: URL(fileURLWithPath: modelFilePath)) else {
                failure("Invalid data")
                return
        }

        Alamofire.upload(multipartFormData: { (form) in
            form.append(modelData, withName: "file", fileName: "result.3dm", mimeType: "application/3dm")
            form.append(productId.data(using: .utf8)!, withName: "productId")
            form.append(printId.data(using: .utf8)!, withName: "printId")
            form.append(customerId.data(using: .utf8)!, withName: "customerid")
        }, to: NetworkManager.API.addToCartPath, encodingCompletion: { result in
            switch result {
            case .success(let upload, _, _):
                upload.responseJSON { response in
                    switch response.result {
                    case .success(let JSON):
                        print("JSON: \(JSON)")
                        success()
                    case .failure(let error):
                        print(error)
                        failure(error.localizedDescription)
                    }
                }
            case .failure(let encodingError):
                failure(encodingError.localizedDescription)
            }
        })

    }

    public func downloadModelTemplate(productId: String,
                                      printId: String,
                                      success: @escaping (URL) -> Void,
                                      failure: @escaping (String) -> Void) {

        guard let customerId = Session.shared.customerId else {
                failure("Invalid data")
                return
        }

        let destination: DownloadRequest.DownloadFileDestination = { _, _ in
            var documentsURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            documentsURL.appendPathComponent("result.zip")
            return (documentsURL, [.removePreviousFile])
        }

        // TODO: use valid productId
        let params = ["customerId": customerId, "productId": /*productId*/"62", "printId": printId]

        Alamofire.download(NetworkManager.API.downloadModelTemplatePath,
                           method: .post,
                           parameters: params,
                           encoding: URLEncoding.default,
                           headers: nil,
                           to: destination).response { (response) in
                            if let error = response.error {
                                failure(error.localizedDescription)
                            } else {
                                if let destinationURL = response.destinationURL {
                                    print(destinationURL)
                                    success(destinationURL)
                                } else {
                                    failure("Unknown error")
                                }
                            }
        }
    }

}
