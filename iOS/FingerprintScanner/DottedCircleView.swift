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

class DottedCircleView: UIView {

    let _border = CAShapeLayer()
    
    required init?(coder aDecoder: NSCoder) {
        super.init(coder: aDecoder)
        setup()
    }
    
    init() {
        super.init(frame: CGRect.zero)
        setup()
    }
    
    func setup() {
        _border.strokeColor = UIColor.white.cgColor
        _border.fillColor = nil
        _border.lineDashPattern = [2, 3]
        _border.lineWidth = 2
        _border.lineJoin = kCALineJoinRound
        self.layer.addSublayer(_border)
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()
        let circleShape = UIBezierPath(roundedRect: self.bounds, cornerRadius:self.bounds.size.width/2)
        var newRect = self.bounds.insetBy(dx: -5, dy: -5)
        circleShape.append(UIBezierPath(roundedRect: newRect, cornerRadius:newRect.size.width/2))
        newRect = newRect.insetBy(dx: -5, dy: -5)
        circleShape.append(UIBezierPath(roundedRect: newRect, cornerRadius:newRect.size.width/2))
  
        newRect = newRect.insetBy(dx: -6, dy: -6)
        circleShape.append(UIBezierPath(roundedRect: newRect, cornerRadius:newRect.size.width/2))
        newRect = newRect.insetBy(dx: -5, dy: -5)
        circleShape.append(UIBezierPath(roundedRect: newRect, cornerRadius:newRect.size.width/2))

        _border.path = circleShape.cgPath
        _border.frame = self.bounds
    }
}
