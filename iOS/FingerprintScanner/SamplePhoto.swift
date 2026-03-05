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
import NYTPhotoViewer

class SamplePhoto: NSObject, NYTPhoto {
    var image: UIImage?
    var imageData: Data?
    var placeholderImage: UIImage?
    let attributedCaptionTitle: NSAttributedString?
    let attributedCaptionSummary: NSAttributedString? = NSAttributedString(string: "")
    let attributedCaptionCredit: NSAttributedString? = NSAttributedString(string: "")

    init(image: UIImage? = nil, imageData: NSData? = nil, attributedCaptionTitle: NSAttributedString) {
        self.image = image
        self.imageData = imageData as Data?
        self.attributedCaptionTitle = attributedCaptionTitle
        
        super.init()
    }
}
