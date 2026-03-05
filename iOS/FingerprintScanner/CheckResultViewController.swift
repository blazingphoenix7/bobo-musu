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
import NYTPhotoViewer
import PopupDialog

class CheckResultViewController: UIViewController {
    @IBOutlet weak var imageViewScanned: UIImageView!
    @IBOutlet weak var imageViewSample: UIImageView!
    var image: UIImage!
    var cropRatio: Float = 0.5
    var dataSourcePhotos: NYTPhotoViewerArrayDataSource?
   
    override func viewDidLoad() {
        super.viewDidLoad()

        imageViewScanned.layer.borderColor = UIColor.white.cgColor
        imageViewScanned.layer.borderWidth = 1
  
        imageViewSample.layer.borderColor = UIColor.white.cgColor
        imageViewSample.layer.borderWidth = 1
        
        if image == nil {
            image = UIImage(named: "\(FingersManager.sharedInstance.fingerprints.count + 1).jpg")
            imageViewSample.image = image
        }

        let hud = MBProgressHUD.showAdded(to: self.view, animated: true)
        hud.mode = MBProgressHUDMode.indeterminate
        hud.label.text = "Image processing..."
        
        DispatchQueue.global(qos: .userInitiated).async {
            self.image = ImageMagicWrapper.processImage(self.image, cropRatio: self.cropRatio).rotate(radians: Float(-Double.pi/2.0))
            DispatchQueue.main.async {
                hud.hide(animated: true)
                self.imageViewScanned.image = self.image
            }
        }
    }

    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
        // Dispose of any resources that can be recreated.
    }
    
    private func showModelSelectionDialog() {
        let message = "Please select model"
        let popup = PopupDialog(title: nil, message: message, image: nil)
        
        var buttons: [PopupDialogButton] = []
        for model in FingersManager.modelsAvailable {
            let button = DefaultButton(title: model.uppercased(), dismissOnTap: false) {
                FingersManager.sharedInstance.model = model
                popup.dismiss(animated: true, completion: {
                    if FingersManager.sharedInstance.fingerprints.count == FingersManager.maxFingerprintCount {
                        self.performSegue(withIdentifier: "showSubmission", sender: self)
                    } else {
                        self.navigationController?.popViewController(animated: true)
                    }
                })
            }
            buttons.append(button)
        }
        
        popup.addButtons(buttons)
        present(popup, animated: true, completion: nil)
    }
    
    @IBAction func useThisPhoto(_ sender: Any) {
        if (FingersManager.sharedInstance.fingerprints.count < FingersManager.maxFingerprintCount) {
            FingersManager.sharedInstance.addFingerprint(image)
        }

        showInputDialog(title: "Enter user name",
                        subtitle: nil,
                        actionTitle: "OK",
                        cancelTitle: "Cancel",
                        inputPlaceholder: "User name",
                        inputKeyboardType: .default,
                        cancelHandler: nil) { (name) in
                            guard let name = name, !name.isEmpty else { return }

                            let hud = MBProgressHUD.showAdded(to: self.view, animated: true)
                            hud.mode = MBProgressHUDMode.indeterminate
                            hud.label.text = "Uploading..."
                            NetworkManager.shared.uploadFingerprint(image: FingersManager.sharedInstance.fingerprints.first!,
                                                                    userName: name, success: {
                                hud.hide(animated: true)
                                self.goToMyPrints()
                            }) { (message) in
                                hud.hide(animated: true)
                                self.showAlert(title: "Uploading error", message: message)
                            }
        }
    }
    
    @IBAction func retakePhoto(_ sender: Any) {
        self.navigationController?.popViewController(animated: true)
    }

    @IBAction func previewPhotoTapped(_ sender: Any) {
        let photo = SamplePhoto(image: self.image, attributedCaptionTitle: NSAttributedString(string:""))
        let dataSource = NYTPhotoViewerArrayDataSource(photos: [photo])
        let photosViewController = PreviewPhotoViewController(dataSource: dataSource)
        photosViewController.rightBarButtonItem = nil
        present(photosViewController, animated: true, completion: nil)
    }

}
