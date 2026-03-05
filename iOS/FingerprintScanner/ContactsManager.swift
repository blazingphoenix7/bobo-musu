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
import SwiftyContacts
import Contacts

class ContactsManager: NSObject {
    class func contactsToJson(contacts: [CNContact]) -> String? {
        var contactsDict: [[String:Any]] = []
        for contact in contacts {
            var contactDict = [String:Any]()
            contactDict["identifier"] = contact.identifier;
            contactDict["name"] = [contact.givenName, contact.familyName].flatMap( {$0} ).joined(separator: " ")
            if let email = contact.emailAddresses.first?.value as String? {
                contactDict["email"] = email
            }
            if let phone = contact.phoneNumbers.first?.value.stringValue {
                contactDict["phone"] = phone
            }

            contactsDict.append(contactDict)
        }

        guard let data = try? JSONSerialization.data(withJSONObject: contactsDict, options: JSONSerialization.WritingOptions.prettyPrinted) else {
            return nil
        }

        return  String(data: data, encoding: String.Encoding.utf8)
    }

    class func retriveContacts(_ completion:@escaping ((String?, String?) -> Void)) {
        let retrieveContacts = {
            fetchContacts(completionHandler: { (result) in
                switch result{
                case .Success(response: let contacts):
                    DispatchQueue.main.async {
                        completion(self.contactsToJson(contacts: contacts), nil)
                    }
                    break
                case .Error(error: let error):
                    DispatchQueue.main.async {
                        completion(nil, error.localizedDescription)
                    }
                    break
                }
            })
        }

        authorizationStatus { (status) in
            switch status {
            case .authorized:
                retrieveContacts()
                break
            case .notDetermined:
                requestAccess { (responce) in
                    if responce{
                        retrieveContacts()
                    } else {
                        DispatchQueue.main.async {
                            completion(nil, "denied")
                        }
                    }
                }
            case .denied:
                DispatchQueue.main.async {
                    completion(nil, "denied")
                }
                break
            default:
                break
            }
        }
    }

}
