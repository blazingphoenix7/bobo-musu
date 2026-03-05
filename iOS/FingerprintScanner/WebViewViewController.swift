//  WebViewController.swift
//  FingerprintScanner
//
//  Created by App on 1/29/19.
//  Copyright © 2019 FSStudio. All rights reserved.
//

import UIKit
import WebKit
import Foundation
import MBProgressHUD
import Zip
import PopupDialog

class WebViewViewController: UIViewController, WKScriptMessageHandler {
    var webView: WKWebView!
    @IBOutlet weak var activityIndicator: UIActivityIndicatorView!

    var urlView: String?
    var urlBaseView: String = NetworkManager.API.host
    var fingerImageUrl = ""
    var outputPath : NSString?
    var printImage: UIImage?

    override func viewDidLoad() {
        super.viewDidLoad()

        NotificationCenter.default.addObserver(self, selector: #selector(keyboardWillHide(_:)), name: NSNotification.Name.UIKeyboardWillHide, object: nil)

        let contentController = WKUserContentController()
        contentController.add(
            self,
            name: "jsHandler"
        )

        let config = WKWebViewConfiguration()
        config.userContentController = contentController
        webView = WKWebView(
            frame: .zero,
            configuration: config
        )
        webView.navigationDelegate = self
        webView.scrollView.isScrollEnabled = true
        view.insertSubview(webView, belowSubview: activityIndicator)
        webView.bindFrameToSuperviewBounds(insets: UIEdgeInsetsMake(UIApplication.shared.statusBarFrame.height, 0, 0, 0))
        if(urlView == nil) {
            urlView = urlBaseView ;
            if let customerId = Session.shared.customerId {
                urlView = urlBaseView + "/directlogin?returnurl=home&customerid="+customerId
            }
        }
        else {
            urlView = urlBaseView + "/" + urlView!
        }


        let url = URL(string: urlView!)
        let req = URLRequest(url: url!)
        self.webView!.load(req)
    }

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        if message.name == "jsHandler" {
            print(message.body)
            let dictionary = jsonParseDictionary(string: message.body as! String);
            let actionName = dictionary["actionName"] as? String;
            if(actionName == "addNewPrint") {
                FingersManager.sharedInstance.clear()
                if let returnUrl = dictionary["returnUrl"] as? String {
                    Session.shared.returnUrl = returnUrl
                }
                let containerVC = UIStoryboard(name: "Main", bundle: nil).instantiateViewController(withIdentifier: "ContainerViewController") as! ContainerViewController
                self.present(containerVC, animated: true, completion: nil)
            }
            else if actionName == "setLoginCustomerId" {
                if let customerId = dictionary["loginCustomerId"] as? String {
                    Session.shared.customerId = customerId
                }
            }
            else if actionName == "setLogout" {
                Session.shared.customerId = nil;
            }
            else if actionName == "printPreview" {
                guard let productId = dictionary["postData"]?["productId"] as? Int,
                    let imagePath = dictionary["postData"]?["printImagePath"] as? String,
                    let printId = dictionary["postData"]?["printId"] as? String else { return }
                  self.fingerImageUrl = urlBaseView + imagePath

                  self.showModelSelectionDialog(productId: String(productId), printId: printId)

                // showPrintPreview(productId: String(productId), printId: printId)
            }
            else if actionName == "getPhoneContacts" {
                ContactsManager.retriveContacts({(contactJson, err) in
                    guard err == nil else {
                        print(err);
                        return;
                    }
                    //print(contactJson);
                    var json = contactJson?.replacingOccurrences(of: "\n", with: "\\n");
                    json = json?.replacingOccurrences(of: "\r", with: "");
                    json = json?.replacingOccurrences(of: "\'", with: "\\\'");
                    json = json?.replacingOccurrences(of: "\"", with: "\\\"");
                    json = self.removeSpecialCharsFromJsonString(text: json!);
                    print(json);
                    self.webView.evaluateJavaScript("loadContactsInUserPhone('\(json ?? "")');") { result, err in
                        guard err == nil else {
                            print(err);
                            return;
                        }
                    }
                    return;
                });
            }
        }
    }


    func jsonParseDictionary(string: String) -> [String: AnyObject]{
        if let data = string.data(using: String.Encoding.utf8){
            do{
                if let dictionary = try JSONSerialization.jsonObject(with: data, options: JSONSerialization.ReadingOptions.mutableLeaves) as? [String: AnyObject]{
                    return dictionary;
                }
            } catch {
                print("Error info: \(error)");
            }
        }
        return [String: AnyObject]()
    }

    func removeSpecialCharsFromJsonString(text: String) -> String {
        let okayChars = Set("abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLKMNOPQRSTUVWXYZ1234567890+-=().!_'\"][{}\\,:@")
        return text.filter {okayChars.contains($0) }
    }



    //For popup to select model
    private func showModelSelectionDialog(productId: String, printId: String) {
        let message = "Please select model"
        let popup = PopupDialog(title: nil, message: message, image: nil)

        var buttons: [PopupDialogButton] = []
        for model in FingersManager.modelsAvailable {
            let button = DefaultButton(title: model.uppercased(), dismissOnTap: false) {
                FingersManager.sharedInstance.model = model
                popup.dismiss(animated: true, completion: {
                    self.showPrintPreview(productId: productId, printId: printId)
                })
            }
            buttons.append(button)
        }

        popup.addButtons(buttons)
        present(popup, animated: true, completion: nil)
    }

    func showPrintPreview(productId: String, printId: String) {
        guard let documentsPath = NSSearchPathForDirectoriesInDomains(.documentDirectory, .userDomainMask, true).first else { return }

        let hud = MBProgressHUD.showAdded(to: self.view, animated: true)
        hud.mode = MBProgressHUDMode.indeterminate
        hud.label.text = "Downloading data..."

        let urlString = self.fingerImageUrl.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed)

        let url = URL(string: urlString!)
        let data = try? Data(contentsOf: url!)
        if data != nil {
            DispatchQueue.main.async {
                self.printImage = UIImage(data: data!)

                let generatePreviewBlock = {

                    let modelName = FingersManager.sharedInstance.model
                    let temp_path = Bundle.main.path(forResource: modelName, ofType: ".3dm")
                    let con_path = Bundle.main.path(forResource: modelName, ofType: ".plist")
                    let outputFile = documentsPath.appending(path: "result.3dm")

                    hud.label.text = "Creating 3D model..."

                    DispatchQueue.global(qos: .userInitiated).async {
                        Model3DManager.shared()?.createModel(fromFingerImage:(self.printImage), //UIImage(contentsOfFile: documentsPath.appending(path: imageFile!)),
                            templatePath: temp_path,//documentsPath.appending(path: "template.3dm"),
                            configPath: con_path,//documentsPath.appending(path: con_path!),
                            outputFile: outputFile)

                        DispatchQueue.main.async {
                            hud.hide(animated: true)

                            let storyboard = UIStoryboard(name: "Main", bundle: nil)
                            let controller = storyboard.instantiateViewController(withIdentifier: "Preview3DModelViewController") as! Preview3DModelViewController
                            controller.modelPath = outputFile
                            controller.didAddToCart = { [weak self, weak controller] in
                                guard let strongSelf = self,
                                    let strongController = controller,
                                    let modelFile = NSSearchPathForDirectoriesInDomains(.documentDirectory, .userDomainMask, true).first?.appending(path: "result.3dm")
                                    else { return }

                                let hud = MBProgressHUD.showAdded(to: strongController.view, animated: true)
                                hud.mode = MBProgressHUDMode.indeterminate
                                hud.label.text = "Uploading..."

                                NetworkManager.shared.addToCart(modelFilePath: modelFile,
                                                                productId: productId,
                                                                printId: printId,
                                                                success: {
                                                                    hud.hide(animated: true)
                                                                    strongController.dismiss(animated: true) {
                                                                        strongSelf.goToCart(animated: false)
                                                                    }
                                },
                                                                failure: { (message) in
                                                                    hud.hide(animated: true)
                                                                    strongSelf.showAlert(title: nil, message: message)
                                })
                            }

                            self.present(controller, animated: true)
                        }

                    }
                }
                generatePreviewBlock()
            }
        }


        //        NetworkManager.shared.downloadModelTemplate(productId: productId,
        //                                                    printId: printId,
        //                                                    success: { destinationUrl in
        //
        //                                                        do {
        //                                                            hud.label.text = "Unpacking..."
        //                                                            try Zip.unzipFile(destinationUrl, destination: URL(string: documentsPath)!, overwrite: true, password: nil)
        //                                                            generatePreviewBlock()
        //                                                        }
        //                                                        catch {
        //                                                            hud.hide(animated: true)
        //                                                            self.showAlert(title: nil, message: "Invalid zip file")
        //                                                        }
        //        }) { message in
        //            self.showAlert(title: nil, message: message)
        //        }
    }


}


extension WebViewViewController: WKNavigationDelegate {
    func webView(_ webView: WKWebView, didStartProvisionalNavigation navigation: WKNavigation!) {
        activityIndicator.isHidden = false
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        activityIndicator.isHidden = true
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        activityIndicator.isHidden = true
    }

}

//MARK: keyboard fix

extension WebViewViewController {
    @objc func keyboardWillHide(_ notification: Notification) {
        // webView.scrollView.setContentOffset(.zero, animated: true)
    }
}


