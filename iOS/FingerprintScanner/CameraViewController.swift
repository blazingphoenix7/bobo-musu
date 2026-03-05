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
import DKCamera
import AVFoundation
import JPSVolumeButtonHandler

class CameraViewController: UIViewController {
    private let showCheckResultSeque = "showCheckResult"
    private let delayNextTip = 5

    @IBOutlet weak var viewCameraContainer: UIView!
    @IBOutlet weak var viewOverlay: UIView!
    @IBOutlet weak var viewBackgound: UIVisualEffectView!
    @IBOutlet weak var labelCounter: UILabel!
    @IBOutlet weak var buttonShowInstructions: UIButton!
    @IBOutlet weak var labelTip: UILabel!
    private var camera: DKCamera!
    private var imageScanned: UIImage!
    private var tipCounter = 0
    private var volumeButtonHandler: JPSVolumeButtonHandler!
    
    private let tips = ["Using small movements, move your finger closer and farther from the camera.",
                        "Try to capture the most interesting aspects of the fingerprint.",
                        "Take the photo against a solid background."]

    override func viewDidLoad() {
        super.viewDidLoad()
 
//        if !PrefsManager.sharedInstance.instructionsShowed {
//            self.slideMenuController()?.openLeft()
//            PrefsManager.sharedInstance.instructionsShowed = true
//        }
        
        labelCounter.layer.cornerRadius = 0.5 * labelCounter.bounds.size.height
        labelCounter.layer.borderColor = UIColor.white.cgColor
        labelCounter.layer.borderWidth = 1

        let delayTime = DispatchTime.now() + .seconds(delayNextTip)
        DispatchQueue.main.asyncAfter(deadline: delayTime) {
            self.fadeInOutTips()
        }
        
        let block = { () -> Void in
            self.camera.takePicture()
        }
        volumeButtonHandler = JPSVolumeButtonHandler(up: block, downBlock: block)
    }

    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
        // Dispose of any resources that can be recreated.
    }
    
    open override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
      
        if let _ = camera {
            camera.view.removeFromSuperview()
        }
        setupCamera()
        if let _ = camera {
            camera.viewWillAppear(animated)
        }
        
        updateCounter()
        
        volumeButtonHandler.start(true)
    }
    
    open override func viewDidDisappear(_ animated: Bool) {
        super.viewDidDisappear(animated)
        
        if let _ = camera {
            camera.viewDidDisappear(animated)
        }
    }
    
    override func viewWillDisappear(_ animated: Bool) {
        volumeButtonHandler.stop()
        super.viewWillDisappear(animated)
    }
    
    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        if let _ = camera {
            camera.viewDidLayoutSubviews()
        }

        let maskLayer = CAShapeLayer()
        maskLayer.path = UIBezierPath(roundedRect: buttonShowInstructions.bounds, byRoundingCorners: [.bottomRight, .topRight], cornerRadii: CGSize(width: buttonShowInstructions.bounds.size.height, height: buttonShowInstructions.bounds.size.height)).cgPath
        buttonShowInstructions.layer.mask = maskLayer
        
        DispatchQueue.main.async(execute: {
            self.setupFingerArea()
        })
    }
    
    override func prepare(for segue: UIStoryboardSegue, sender: Any?) {
        if segue.identifier == showCheckResultSeque {
            if let controller = segue.destination as? CheckResultViewController {
                controller.image = imageScanned
                
                if let imageScanned = imageScanned {
                    let fillRectSize = Utils.calcAspectFillRect(viewCameraContainer.bounds, size: imageScanned.size)
                    let frameImageView = CGRect(x: viewCameraContainer.bounds.size.width - fillRectSize.width,
                                                y: viewCameraContainer.bounds.size.height - fillRectSize.height,
                                                width: fillRectSize.width,
                                                height: fillRectSize.height)
                    let viewToCalculate = UIView(frame:frameImageView)
                    let resultRect = viewCameraContainer.convert(viewOverlay.frame, to: viewToCalculate)
                    
                    controller.cropRatio = Float(resultRect.size.width/min(viewToCalculate.frame.size.width, viewToCalculate.frame.size.height))
                }
            }
        }
    }

    private func setupCamera() {
        if DKCamera.isAvailable() {
            camera = DKCamera()
            if let cameraView = camera.view {
                addChildViewController(camera)
                self.viewCameraContainer.addSubview(cameraView)
                camera.didMove(toParentViewController: self)
                
                camera.view?.translatesAutoresizingMaskIntoConstraints = false
                let views = ["camera": cameraView]
                self.viewCameraContainer?.addConstraints(NSLayoutConstraint.constraints(withVisualFormat: "H:|[camera]|", options: [], metrics: nil, views: views))
                self.viewCameraContainer?.addConstraints(NSLayoutConstraint.constraints(withVisualFormat: "V:|[camera]|", options: [], metrics: nil, views: views))
            }
        
            disableAutofocus()
            
            camera.showsCameraControls = false
            camera.flashMode = .on
            camera.didFinishCapturingImage = {(image, metadata) in
                self.imageScanned = image
                self.performSegue(withIdentifier: self.showCheckResultSeque, sender: self)
            }

        }
    }
    
    private func disableAutofocus() {
        if let currentDevice = camera.currentDevice {
            try! currentDevice.lockForConfiguration()
            currentDevice.setFocusModeLocked(lensPosition: 0.1, completionHandler: nil)
            currentDevice.unlockForConfiguration()
        }

    }
    
    private func setupFingerArea() {
//        let roundedRect = self.viewOverlay.frame
//        let cornerRadius = roundedRect.size.height / 2.0;
//
//        let path = UIBezierPath(rect: self.view.bounds)
//        let croppedPath = UIBezierPath(roundedRect: roundedRect, cornerRadius: cornerRadius)
//        path.append(croppedPath)
//        path.usesEvenOddFillRule = true
//
//        let maskLayer = CAShapeLayer()
//        maskLayer.path = path.cgPath;
//        maskLayer.fillRule = kCAFillRuleEvenOdd
//
//        if #available(iOS 11.0, *) {
//            viewBackgound.layer.mask = maskLayer
//        } else {
//            let maskView = UIView(frame: self.view.bounds)
//            maskView.backgroundColor = .black
//            maskView.layer.mask = maskLayer
//            viewBackgound.mask = maskView
//        }
    }
    
    private func updateCounter() {
        let current = FingersManager.sharedInstance.fingerprints.count + 1
        let max = FingersManager.maxFingerprintCount
        self.labelCounter.text = "\(current) of \(max)"
    }
    
    @IBAction func scanTapped(_ sender: Any) {
        if DKCamera.isAvailable() {
           camera.takePicture()
        } else {
            self.performSegue(withIdentifier: self.showCheckResultSeque, sender: self)
        }
    }
    
    @IBAction func showInstructions(_ sender: Any) {
        self.slideMenuController()?.openLeft()
    }
    
    @IBAction func close(_ sender: Any) {
        dismiss(animated: true, completion: nil)
    }
    
    private func fadeInOutTips() {
        tipCounter += 1
        if tipCounter == self.tips.count {
            tipCounter = 0
        }
        
        let animationDuration = 0.5
        
        UIView.animate(withDuration: animationDuration, animations: { () -> Void in
            self.labelTip.alpha = 0
        }) { (Bool) -> Void in
            self.labelTip.text = self.tips[self.tipCounter]
            UIView.animate(withDuration: animationDuration, delay: 0.5, options: .curveEaseInOut, animations: { () -> Void in
                self.labelTip.alpha = 1
            }, completion: { (Bool) -> Void in
                let delayTime = DispatchTime.now() + .seconds(self.delayNextTip)
                DispatchQueue.main.asyncAfter(deadline: delayTime) {
                    self.fadeInOutTips()
                }
            })
        }
    }
}
