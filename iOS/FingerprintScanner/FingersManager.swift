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
import MessageUI
import Zip

class FingersManager: NSObject {
//    static let emailToSend = "sarah@sarahgraham.com"
    static let emailToSend = "tim@fsstudio.com"
    static let modelsAvailable = ["oval", "pear", "ring"]

    static let maxFingerprintCount = 1
    public var fingerprints: [UIImage] = []
    public var zipFile: String?
    public var model: String?
    var successBlock: (() -> Void)?
    var failureBlock: ((String) -> Void)?
    
    static let sharedInstance = FingersManager()
    
    public func clear() {
        fingerprints.removeAll()
    }
    
    public func addFingerprint(_ image: UIImage) {
        fingerprints.append(image)
    }

    public func createModel(from image: UIImage,
                            model: String,
                            outputFile: String,
                            success: @escaping () -> Void,
                            failure: @escaping (String) -> Void) {
        if !Model3DManager.shared().createModel(fromFingerImage: image, modelName: model, outputFile: outputFile) {
            failure("Something went wrong")
            return
        }

        success()
    }

    public func createModelAndPack(success: @escaping () -> Void, failure: @escaping (String) -> Void) {
        let documentsPath = NSSearchPathForDirectoriesInDomains(.documentDirectory, .userDomainMask, true).first
        let outpuFile = documentsPath?.appending(path: "result.3dm")
        if !Model3DManager.shared().createModel(fromFingerImage: fingerprints.first, modelName: model, outputFile: outpuFile) {
            failure("Something went wrong")
            return
        }

        #if OPENGL_VIEWER
        success()
        #else
        do {
            let zipFilePath = documentsPath?.appending(path: "archive.zip")
            try Zip.zipFiles(paths: [URL(string: outpuFile!)!], zipFilePath: URL(string: zipFilePath!)!, password: nil, progress: nil)
            zipFile = zipFilePath
            success()
        }
        catch {
            failure("Something went wrong")
        }
        #endif
    }
    
    public func sendMail(fromController: UIViewController, info:SendMailInfo, success: @escaping () -> Void, failure: @escaping (String) -> Void) {
        self.successBlock = success
        self.failureBlock = failure
        if MFMailComposeViewController.canSendMail() {
            let mail = MFMailComposeViewController()
            mail.mailComposeDelegate = self
            //mail.setToRecipients(["sarah@sarahgraham.com"])
            mail.setToRecipients([FingersManager.emailToSend])
            if let userName = info.userName, let subjectName = info.subjectName, let email = info.email {
                mail.setSubject("\(userName)'s order with \(subjectName) fingerprints")
                mail.setMessageBody("**Choose \"Actual Size\" option for sending the images, if you are asked.\n\nnOrder from: \(userName)\nSubject name: \(subjectName)\nEmail address: \(email)", isHTML: false)
                let zipData = try? Data(contentsOf: URL(fileURLWithPath: zipFile!))
                let imageName = "\(userName)_\(subjectName)_print.zip"
                mail.addAttachmentData(zipData!, mimeType: "application/zip", fileName: imageName)
            }
        
            fromController.present(mail, animated: true)
        } else {
            failureBlock!("You can't send email because you don't have any email account configured on this device.")
        }
    }
}

extension FingersManager : MFMailComposeViewControllerDelegate {
    func mailComposeController(_ controller: MFMailComposeViewController, didFinishWith result: MFMailComposeResult, error: Error?) {
        controller.dismiss(animated: true) { 
            if error == nil {
                self.successBlock!()
            } else {
                self.failureBlock!((error?.localizedDescription)!)
            }
        }
    }
}
