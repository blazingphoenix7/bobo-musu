package com.crowdbotics.bobomusu.Activity;

import android.Manifest;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.app.ProgressDialog;
import android.content.BroadcastReceiver;
import android.content.ContentResolver;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.os.StrictMode;
import android.provider.ContactsContract;
import android.os.Bundle;
import android.util.Log;
import android.view.KeyEvent;
import android.view.View;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;

import com.crowdbotics.bobomusu.BuildConfig;
import com.crowdbotics.bobomusu.Networking.NetworkManager;
import com.crowdbotics.bobomusu.Networking.WebviewClient;
import com.crowdbotics.bobomusu.R;
import com.crowdbotics.bobomusu.Utils.RequestUserPermission;
import com.progressbar_lib.cc.cloudist.acplibrary.ACProgressConstant;
import com.progressbar_lib.cc.cloudist.acplibrary.ACProgressFlower;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;

public class WebviewActivity extends AppCompatActivity implements View.OnClickListener {

    private WebView webView = null;
    private ACProgressFlower dialog = null;
    private String urlview = "";
private TextView tv_takePicture;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_webview);
       /* RequestUserPermission rp=new RequestUserPermission(this);
        rp.verifyStoragePermissions();*/
        webView = (WebView) findViewById(R.id.webview);
        tv_takePicture = findViewById(R.id.tv_takePicture);
        WebSettings webSettings = webView.getSettings();
        webSettings.setJavaScriptEnabled(true);

        //This can break the user experience of the app users.
        WebviewClient webViewClient = new WebviewClient(this);
        webView.setWebViewClient(webViewClient);
        webView.getSettings().setDomStorageEnabled(true);
        tv_takePicture.setOnClickListener(this);
        //Take Picture
//        webView.addJavascriptInterface(new Object(){
//            @JavascriptInterface
//            public void addNewPrint(String json)
//            {
//                Log.d("addNewPrint", "addNewPrint");
//
//                try{
//                    JSONObject mainObject = new JSONObject(json);
//                    String returnUrl = mainObject.getString("returnUrl");
//
//                    SharedPreferences.Editor editor = getSharedPreferences("URLInfo", MODE_PRIVATE).edit();
//                    editor.putString("returnUrl", returnUrl);
//                    editor.apply();
//
//                    Intent mIntent = new Intent(WebviewActivity.this, CameraviewActivity.class);
//                    startActivity(mIntent);
//                }
//                catch (JSONException e){
//                    e.printStackTrace();
//                }
//            }
//        },"webview");
        //Take Picture
        webView.addJavascriptInterface(new Object(){
            @JavascriptInterface
            public void takepicture(String json)
            {
                try{
                    JSONObject mainObject = new JSONObject(json);
                    String returnUrl = mainObject.getString("returnUrl");

                    SharedPreferences.Editor editor = getSharedPreferences("URLInfo", MODE_PRIVATE).edit();
                    editor.putString("returnUrl", returnUrl);
                    editor.apply();

                    Intent mIntent = new Intent(WebviewActivity.this, CameraviewActivity.class);
                    startActivity(mIntent);
                }
                catch (JSONException e){
                    e.printStackTrace();
                }
            }
        },"webview");

        //Login customerID getting
        webView.addJavascriptInterface(new Object(){
            @JavascriptInterface
            public void getLogincustomerID(String json)
            {
                try {
                    JSONObject mainObject = new JSONObject(json);
                    String loginCustomerId = mainObject.getString("loginCustomerId");

                    SharedPreferences.Editor editor = getSharedPreferences("LoginInfo", MODE_PRIVATE).edit();
                    editor.putString("UserID", loginCustomerId);
                    editor.apply();

                } catch (JSONException e) {
                    e.printStackTrace();
                }
                Log.d("Jsontest", json);
            }
        },"webview");

        //get phone contacts
        webView.addJavascriptInterface(new Object(){
            @JavascriptInterface
            public void getPhoneContacts()
            {
                if(checkPermission()){
                    readContacts();
                }
                else {
                    getPermissionToReadUserContacts();
                }
            }
        },"message");

        //Log Out Setting
        webView.addJavascriptInterface(new Object(){
            @JavascriptInterface
            public void setLogout()
            {
                SharedPreferences.Editor editor = getSharedPreferences("LoginInfo", MODE_PRIVATE).edit();
                editor.putString("UserID", "");
                editor.apply();
            }
        },"Logout");

        //get login info from sharedpreference
        urlview = getIntent().getStringExtra("URLinfo");
        SharedPreferences login_prefs = getSharedPreferences("LoginInfo", MODE_PRIVATE);
        String user_id = login_prefs.getString("UserID", "");

        if(urlview == null){
            if(user_id == ""){
               // urlview = NetworkManager.host + "/signin";
                urlview = NetworkManager.host + "/login";
            }


            else{
                urlview = NetworkManager.host + "/directlogin?returnurl=home&customerid=" + user_id;
            }

        }
        else{
            urlview = NetworkManager.host + "/" + urlview;
        }

        //load the url of site
        webView.loadUrl(urlview);

        dialog = new ACProgressFlower.Builder(this)
                .sizeRatio(0.15f)
                .petalThickness(5)
                .direction(ACProgressConstant.DIRECT_CLOCKWISE)
                .themeColor(Color.WHITE)
                .text("")
                .fadeColor(android.R.color.transparent).build();

        //check page starting and finishing
        webView.setWebViewClient(new WebViewClient() {
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                try{
                    dialog.show();
                }
                catch (Exception e){
                    e.printStackTrace();
                }
            }
            public void onPageFinished(WebView view, String url) {
                try{
                    dialog.dismiss();
                }
                catch (Exception e){
                    e.printStackTrace();
                }
            }
        });
    }

    private boolean checkPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_CONTACTS)
                != PackageManager.PERMISSION_GRANTED) {
            // Permission is not granted
            return false;
        }
        return true;
    }

    // Called when the user is performing an action which requires the app to read the
    // user's contacts
    public void getPermissionToReadUserContacts() {

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_CONTACTS)
                != PackageManager.PERMISSION_GRANTED) {

            if (shouldShowRequestPermissionRationale(
                    Manifest.permission.READ_CONTACTS)) {
            }

            // Fire off an async request to actually get the permission
            // This will show the standard permission request dialog UI
            requestPermissions(new String[]{Manifest.permission.READ_CONTACTS},
                    1);
        }
    }

    // Callback with the request from calling requestPermissions(...)
    @Override
    public void onRequestPermissionsResult(int requestCode,
                                           @NonNull String permissions[],
                                           @NonNull int[] grantResults) {
        // Make sure it's our original READ_CONTACTS request
        if (requestCode == 1) {
            if (grantResults.length == 1 &&
                    grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "Read Contacts permission granted", Toast.LENGTH_SHORT).show();
                readContacts();
            } else {
                Toast.makeText(this, "Read Contacts permission denied", Toast.LENGTH_SHORT).show();
            }
        } else {
            super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        }
    }

    public void readContacts(){

        ContentResolver cr = getContentResolver();
        Cursor cur = cr.query(ContactsContract.Contacts.CONTENT_URI,
                null, null, null, null);

        final JSONArray jsonArray = new JSONArray();
        JSONObject obj = null;

        if (cur.getCount() > 0) {
            while (cur.moveToNext()) {

                obj = new JSONObject();

                //get contact Info
                String id = cur.getString(cur.getColumnIndex(ContactsContract.Contacts._ID));
                String name = cur.getString(cur.getColumnIndex(ContactsContract.Contacts.DISPLAY_NAME));
                String email = "";
                String phone = "";

                if (Integer.parseInt(cur.getString(cur.getColumnIndex(ContactsContract.Contacts.HAS_PHONE_NUMBER))) > 0) {

                    // get the phone number
                    Cursor pCur = cr.query(ContactsContract.CommonDataKinds.Phone.CONTENT_URI,null,
                            ContactsContract.CommonDataKinds.Phone.CONTACT_ID +" = ?",
                            new String[]{id}, null);
                    while (pCur.moveToNext()) {
                        phone = pCur.getString(
                                pCur.getColumnIndex(ContactsContract.CommonDataKinds.Phone.NUMBER));
                    }
                    pCur.close();


                    // get email and type
                    Cursor emailCur = cr.query(
                            ContactsContract.CommonDataKinds.Email.CONTENT_URI,
                            null,
                            ContactsContract.CommonDataKinds.Email.CONTACT_ID + " = ?",
                            new String[]{id}, null);
                    while (emailCur.moveToNext()) {
                        // This would allow you get several email addresses
                        // if the email addresses were stored in an array
                        email = emailCur.getString(
                                emailCur.getColumnIndex(ContactsContract.CommonDataKinds.Email.DATA));
                    }
                    emailCur.close();

                    try {
                        obj.put("identifier", id);
                        obj.put("name", name);
                        if(email != ""){
                            obj.put("email", email);
                        }
                        if(phone != ""){
                            obj.put("phone", phone);
                        }

                    } catch (JSONException e) {
                        // TODO Auto-generated catch block
                        e.printStackTrace();
                    }
                }

                jsonArray.put(obj);
            }
        }

        webView.post(new Runnable() {
            @Override
            public void run() {
                webView.loadUrl("javascript:loadContactsInUserPhone('" + jsonArray + "')");
            }
        });
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if ((keyCode == KeyEvent.KEYCODE_BACK) && this.webView.canGoBack()) {
            this.webView.goBack();
            return true;
        }

        return super.onKeyDown(keyCode, event);
    }

    @Override
    public void onClick(View v) {
        if (v==tv_takePicture){
            try {
                if(isPackageInstalled("org.opencv.engine",getPackageManager())){

                    Intent mIntent = new Intent(WebviewActivity.this, CameraviewActivity.class);
                    startActivity(mIntent);
                }

                else{
                    downloadapk();

                }
            } catch (Exception e) {
                e.printStackTrace();
            }


        }
    }
    private boolean isPackageInstalled(String packageName, PackageManager packageManager) {
        try {
            packageManager.getPackageInfo(packageName, 0);
            return true;
        } catch (PackageManager.NameNotFoundException e) {
            return false;
        }
    }
    ProgressDialog progressDialog;
    private void downloadapk(){
        File file = new File(Environment.getExternalStorageDirectory() + "/Download" + "/OpenCV_Manager.apk");
        if(file.exists()){
            new AlertDialog.Builder(WebviewActivity.this)
                    .setMessage("You need to install Open CV Manager to use this feature , Please install this app from Download/OpenCV_Manager.apk.")
                    .setNegativeButton("Ok", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    dialog.dismiss();
                }
            }).show();
        }

else
        {
            progressDialog = new ProgressDialog(this);
            progressDialog.setCancelable(false);
            new AlertDialog.Builder(this).setTitle("Attention!!")
                    .setMessage("You need to download and install Open CV Manager to use this feature , Please download and install this app")
                    .setPositiveButton("Download", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {

                    progressDialog.setMessage("Downloading");
                    progressDialog.show();
                    BroadcastReceiver onComplete=new BroadcastReceiver() {
                        public void onReceive(Context ctxt, Intent intent) {
                            new AlertDialog.Builder(WebviewActivity.this)
                                    .setMessage("You need to install Open CV Manager to use this feature , Please install this app from Download/OpenCV_Manager.apk.").setNegativeButton("Ok", new DialogInterface.OnClickListener() {
                                @Override
                                public void onClick(DialogInterface dialog, int which) {
                                    dialog.dismiss();
                                }
                            }).show();
                            progressDialog.dismiss();
                        }
                    };
                    registerReceiver(onComplete, new IntentFilter(DownloadManager.ACTION_DOWNLOAD_COMPLETE));

                    DownloadManager downloadmanager = (DownloadManager) getSystemService(Context.DOWNLOAD_SERVICE);
                    Uri uri = Uri.parse("http://iphtechnologies.com.au/OpenCV_Manager.apk");
                    DownloadManager.Request request = new DownloadManager.Request(uri);
                    request.setTitle("My File");
                    request.setDescription("Downloading");
                    request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
                    request.setVisibleInDownloadsUi(false);
                    request.setDestinationUri(Uri.parse("file://"+Environment.getExternalStorageDirectory() + "/Download" + "/OpenCV_Manager.apk"));
                    downloadmanager.enqueue(request);

                }
            }).setNegativeButton("Cancel", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    dialog.dismiss();
                }
            }).show();

        }

    }

    private void installApk() throws NoSuchMethodException, InvocationTargetException, IllegalAccessException {


        StrictMode.VmPolicy.Builder builder = new StrictMode.VmPolicy.Builder();
        StrictMode.setVmPolicy(builder.build());



        File toInstall = new File(Environment.getExternalStorageDirectory() + "/BoboMoso/" + "OpenCV_Manager.apk");
        Intent intent;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                boolean result = getPackageManager().canRequestPackageInstalls();
            }

/*           Uri apkUri = FileProvider.getUriForFile(this, BuildConfig.APPLICATION_ID + ".fileprovider", toInstall);
            intent = new Intent(Intent.ACTION_INSTALL_PACKAGE);
            intent.setData(apkUri);
            intent.setFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
            startActivity(intent);*/
            Method m = StrictMode.class.getMethod("disableDeathOnFileUriExposure");
            m.invoke(null);
            Intent promptInstall = new Intent(Intent.ACTION_INSTALL_PACKAGE)
                    .setDataAndType(Uri.parse("file://"+Environment.getExternalStorageDirectory() + "/BoboMoso/" + "OpenCV_Manager.apk"),
                            "application/vnd.android.package-archive");
            promptInstall.setFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            promptInstall.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
           promptInstall.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
            startActivity(promptInstall);
        } else {
            Uri apkUri = Uri.fromFile(toInstall);
            intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(apkUri, "application/vnd.android.package-archive");
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(intent);
        }
       // startActivity(intent);
calculateArea(30.0);
    }
    static { System.loadLibrary("native-lib");}
    private native String calculateArea(double radius);
 private native String Dump3dmFileHelper1   (double radius);


}
