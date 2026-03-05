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

class Utils: NSObject {
    class func calcAspectFitRect(_ rect: CGRect, size: CGSize) -> CGSize {
        var szRet = CGSize(width: rect.size.width, height: max(1, rect.size.height))
        let dFactor = szRet.width / szRet.height
        if size.height * dFactor > size.width {
            szRet.width = szRet.height*size.width / max( 1, size.height)
        } else {
            szRet.height = szRet.width * size.height / max( 1, size.width )
        }
        return szRet
    }

    class func calcAspectFillRect(_ rect: CGRect, size: CGSize) -> CGSize {
        let wi = size.width
        let hi = size.height
        
        let ws = rect.size.width;
        let hs = rect.size.height;
        
        let rs = ws / hs
        let ri = wi / hi
        if rs < ri {
            return CGSize(width:wi * hs/hi, height:hs)
        }
        
        return CGSize(width:ws, height:hi * ws/wi);
    }
}

 extension String {
    func appending(path: String) -> String {
        let nsSt = self as NSString
        return nsSt.appendingPathComponent(path)
    }
 }
