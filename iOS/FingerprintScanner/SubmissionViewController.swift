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
import MBProgressHUD

class SubmissionViewController: UIViewController {
    private let showConfirmationSeque = "showConfirmation"
    

    @IBOutlet weak var scrollView: UIScrollView!
    var textFieldActive: UITextField?
    @IBOutlet weak var textFieldSubject: RectangularTextField!
    @IBOutlet weak var textFieldYourName: RectangularTextField!
    @IBOutlet weak var textFieldStore: RectangularTextField!
    @IBOutlet weak var textFieldEmail: RectangularTextField!
    var failureMessage: String?

    override func viewDidLoad() {
        super.viewDidLoad()

        #if OPENGL_VIEWER
        textFieldSubject.isHidden = true
        textFieldEmail.isHidden = true
        textFieldStore.isHidden = true
        #endif

        hideKeyboardWhenTappedAround()
        NotificationCenter.default.addObserver(self, selector: #selector(SubmissionViewController.keyboardWillShow(notification:)), name: .UIKeyboardWillShow, object: nil)
        
        if let userName = PrefsManager.sharedInstance.userName {
            textFieldYourName.text = userName
        }
 
        if let store = PrefsManager.sharedInstance.store {
            textFieldStore.text = store
        }

        if let email = PrefsManager.sharedInstance.email {
            textFieldEmail.text = email
        }
    }

    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
        // Dispose of any resources that can be recreated.
    }
    

    override func prepare(for segue: UIStoryboardSegue, sender: Any?) {
        if segue.identifier == showConfirmationSeque {
            if let controller = segue.destination as? ConfirmationViewController {
                controller.failureMessage = self.failureMessage
            }
        }
    }
    
    @objc fileprivate func keyboardWillShow(notification:NSNotification) {
        if let keyboardRectValue = (notification.userInfo?[UIKeyboardFrameEndUserInfoKey] as? NSValue)?.cgRectValue {
            if let textField = textFieldActive {
                let offsetY = textField.frame.origin.y - scrollView.frame.size.height + keyboardRectValue.height + textField.frame.size.height + 10
                if offsetY > 0 {
                    scrollView.setContentOffset(CGPoint(x:0, y:offsetY), animated: true)
                }
            }
        }
    }

    @IBAction func textFieldDidEndEditing(_ sender: Any) {
        scrollView.setContentOffset(CGPoint(x:0, y:0), animated: true)
    }
    
    @IBAction func textFieldDidBeginEditing(_ textField: UITextField) {
        textFieldActive = textField
    }

    @IBAction func textFieldPrimaryActionTriggered(_ textField: UITextField) {
        if textField == textFieldSubject {
            textFieldYourName.becomeFirstResponder()
        } else if textField == textFieldYourName {
            textFieldStore.becomeFirstResponder()
        } else if textField == textFieldStore {
            textFieldEmail.becomeFirstResponder()
        } else if textField == textFieldEmail {
            textFieldEmail.resignFirstResponder()
        }
    }
    
    @IBAction func submit(_ sender: Any) {
        #if !OPENGL_VIEWER
        if (textFieldSubject.text?.isEmpty)! {
            showAlert("Please enter name of subject.")
            return
        }
        #endif

        if (textFieldYourName.text?.isEmpty)! {
            showAlert(title: nil, message: "Please enter your name.")
            return
        }
        
        #if !OPENGL_VIEWER
        if (textFieldEmail.text?.isEmpty)! {
            showAlert(title: nil, message: "Please enter your email address.")
            return
        }

        if (!(textFieldEmail.text?.isValidEmail())!) {
            showAlert(title: nil, message: "Please enter valid email address.")
            return
        }
        #endif

        let hud = MBProgressHUD.showAdded(to: self.view, animated: true)
        hud.mode = MBProgressHUDMode.indeterminate
        hud.label.text = "Creating 3D model..."
        
        PrefsManager.sharedInstance.userName = textFieldYourName.text
        PrefsManager.sharedInstance.store = textFieldStore.text
        PrefsManager.sharedInstance.email = textFieldEmail.text
        
        let info = SendMailInfo()
        info.userName = textFieldYourName.text
        info.subjectName = textFieldSubject.text
        info.store = textFieldStore.text
        info.email = textFieldEmail.text
        failureMessage = nil

        DispatchQueue.global(qos: .userInitiated).async {
            FingersManager.sharedInstance.createModelAndPack(success: {
                DispatchQueue.main.async {
                    hud.hide(animated: true)

                #if OPENGL_VIEWER
                    let storyboard = UIStoryboard(name: "Main", bundle: nil)
                    let controller = storyboard.instantiateViewController(withIdentifier: "Preview3DModelViewController") as! Preview3DModelViewController
                    let documentsPath = NSSearchPathForDirectoriesInDomains(.documentDirectory, .userDomainMask, true).first
                    let outputFile = documentsPath?.appending(path: "result.3dm")
                    controller.modelPath = outputFile
                    controller.didDismiss = { [weak self] in
                        guard let strongSelf = self else { return }

                        let hud = MBProgressHUD.showAdded(to: strongSelf.view, animated: true)
                        hud.mode = MBProgressHUDMode.indeterminate
                        hud.label.text = "Uploading..."
                        // TODO: 3dm uploading
//                        FingersManager.sharedInstance.upload(with: info, from: strongSelf, success: {
//                            hud.hide(animated: true)
//                            strongSelf.performSegue(withIdentifier: strongSelf.showConfirmationSeque, sender: self)
//                        }, failure: { failureString in
//                            hud.hide(animated: true)
//                            strongSelf.failureMessage = failureString
//                            strongSelf.performSegue(withIdentifier: strongSelf.showConfirmationSeque, sender: self)
//                        })
                    }

                    self.present(controller, animated: true)
                #else
                    FingersManager.sharedInstance.sendMail(fromController: self, info: info, success: {
                        self.performSegue(withIdentifier: self.showConfirmationSeque, sender: self)
                    }) { failureString in
                        self.failureMessage = failureString
                        self.performSegue(withIdentifier: self.showConfirmationSeque, sender: self)
                    }
                #endif
                }
            }, failure: { (message) in
                DispatchQueue.main.async {
                    hud.hide(animated: true)
                }

                self.failureMessage = message
                self.performSegue(withIdentifier: self.showConfirmationSeque, sender: self)
            })
        }
    }
}
