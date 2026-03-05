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

class InstructionsViewController: UIViewController {
    @IBOutlet weak var closeButton: UIButton!

    override func viewDidLoad() {
        super.viewDidLoad()
    }

    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
        // Dispose of any resources that can be recreated.
    }

    override func viewDidLayoutSubviews() {
         super.viewDidLayoutSubviews()
        
        let maskLayer = CAShapeLayer()
        maskLayer.path = UIBezierPath(roundedRect: closeButton.bounds, byRoundingCorners: [.bottomRight, .topRight], cornerRadii: CGSize(width: closeButton.bounds.size.height, height: closeButton.bounds.size.height)).cgPath
        closeButton.layer.mask = maskLayer
    }

    @IBAction func closeInstructions(_ sender: Any) {
        self.slideMenuController()?.closeLeft()
    }
}

