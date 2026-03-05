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

class Session: NSObject {
    static var shared = Session()

    private enum Keys: String {
        case customerId = "loginCustomerIdKey"
        case returnUrl = "returnUrlKey"
    }

    var customerId: String? {
        get {
            return UserDefaults.standard.string(forKey: Keys.customerId.rawValue)
        }
        set {
            UserDefaults.standard.set(newValue, forKey: Keys.customerId.rawValue)
            UserDefaults.standard.synchronize()
        }
    }
    
    var returnUrl: String? {
        get {
            return UserDefaults.standard.string(forKey: Keys.returnUrl.rawValue)
        }
        set {
            UserDefaults.standard.set(newValue, forKey: Keys.returnUrl.rawValue)
            UserDefaults.standard.synchronize()
        }
    }

    var isLoggedIn: Bool {
        return customerId != nil
    }

    func logout() {
        customerId = nil
    }
}
