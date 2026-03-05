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
import SlideMenuControllerSwift

class ContainerViewController: SlideMenuController {
    
    override func awakeFromNib() {
        SlideMenuOptions.leftViewWidth = UIScreen.main.bounds.size.width
        SlideMenuOptions.contentViewScale = 1
        SlideMenuOptions.hideStatusBar = false
        
        if let controller = self.storyboard?.instantiateViewController(withIdentifier: "CameraViewControllerNav") {
            self.mainViewController = controller
        }
        if let controller = self.storyboard?.instantiateViewController(withIdentifier: "InstructionsViewController") {
            self.leftViewController = controller
        }
        super.awakeFromNib()
    }
    
    override var preferredStatusBarStyle: UIStatusBarStyle {
        return .lightContent
    }
}
