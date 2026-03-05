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

class PrefsManager: NSObject {
    private let instructionsShowedKey = "instructionsShowed"
    private let userNameKey = "userName"
    private let storeKey = "store"
    private let emailKey = "email"

    static let sharedInstance = PrefsManager()

    var instructionsShowed: Bool {
        get {
            return UserDefaults.standard.bool(forKey: instructionsShowedKey)
        }
        
        set {
            UserDefaults.standard.set(newValue, forKey: instructionsShowedKey)
            UserDefaults.standard.synchronize()
        }
    }
    
    var userName: String? {
        get {
            return UserDefaults.standard.string(forKey: userNameKey)
        }
        
        set {
            UserDefaults.standard.set(newValue, forKey: userNameKey)
            UserDefaults.standard.synchronize()
        }
    }

    var store: String? {
        get {
            return UserDefaults.standard.string(forKey: storeKey)
        }
        
        set {
            UserDefaults.standard.set(newValue, forKey: storeKey)
            UserDefaults.standard.synchronize()
        }
    }

    var email: String? {
        get {
            return UserDefaults.standard.string(forKey: emailKey)
        }
        
        set {
            UserDefaults.standard.set(newValue, forKey: emailKey)
            UserDefaults.standard.synchronize()
        }
    }
}
