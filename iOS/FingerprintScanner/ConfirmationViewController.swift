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

class ConfirmationViewController: UIViewController {
    @IBOutlet weak var labelInfo: UILabel!
    @IBOutlet weak var buttonAction: RoundedButton!
    var failureMessage: String?
    
    override func viewDidLoad() {
        super.viewDidLoad()

        if let failureMessage = failureMessage {
            labelInfo.text = failureMessage
            buttonAction.setTitle("TRY AGAIN", for: .normal)
        }
    }

    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
        // Dispose of any resources that can be recreated.
    }
    

    /*
    // MARK: - Navigation

    // In a storyboard-based application, you will often want to do a little preparation before navigation
    override func prepare(for segue: UIStoryboardSegue, sender: Any?) {
        // Get the new view controller using segue.destinationViewController.
        // Pass the selected object to the new view controller.
    }
    */

    @IBAction func startOver(_ sender: Any) {
        if let _ = failureMessage {
            navigationController?.popViewController(animated: true)
            return;
        }
        
        FingersManager.sharedInstance.clear()
        if let controller = self.storyboard?.instantiateViewController(withIdentifier: "CameraViewController") {
            self.navigationController?.setViewControllers([controller], animated: true)
        }
    }
    
    @IBAction func goToMyPrints(_ sender: Any) {
        if let customerId = UserDefaults.standard.string(forKey: "loginCustomerIdKey") {
            let containerVC = UIStoryboard(name: "Main", bundle: nil).instantiateViewController(withIdentifier: "WebViewViewController") as! WebViewViewController;
            containerVC.urlView = "/directlogin?returnurl=print/myprints&customerid="+customerId;
            self.present(containerVC, animated: true, completion: nil)
        }
    }
 }
