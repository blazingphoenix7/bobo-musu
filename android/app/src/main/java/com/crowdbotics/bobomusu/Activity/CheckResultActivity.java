package com.crowdbotics.bobomusu.Activity;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.RelativeLayout;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

import com.crowdbotics.bobomusu.Networking.NetworkManager;
import com.crowdbotics.bobomusu.R;
import com.loopj.android.http.AsyncHttpClient;
import com.loopj.android.http.AsyncHttpResponseHandler;
import com.loopj.android.http.RequestParams;
import com.progressbar_lib.cc.cloudist.acplibrary.ACProgressConstant;
import com.progressbar_lib.cc.cloudist.acplibrary.ACProgressFlower;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;

public class CheckResultActivity extends AppCompatActivity {

    Bitmap mImgBitmap;
    String mFilePath;
    private ACProgressFlower progressdialog = null;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_check_result);

        mFilePath = getIntent().getStringExtra("image_path");

        try{
            mImgBitmap = BitmapFactory.decodeFile(mFilePath);
        }
        catch (Exception e){
            e.printStackTrace();
        }

        ImageView fingerImgView = (ImageView)findViewById(R.id.finger_img);
        fingerImgView.setImageBitmap(mImgBitmap);

        progressdialog = new ACProgressFlower.Builder(this)
                .sizeRatio(0.15f)
                .petalThickness(5)
                .direction(ACProgressConstant.DIRECT_CLOCKWISE)
                .themeColor(Color.WHITE)
                .text("Uploading")
                .fadeColor(android.R.color.transparent).build();

        TextView retakeBtn = (TextView)findViewById(R.id.retakeBtn);
        retakeBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent mIntent = new Intent(CheckResultActivity.this, CameraviewActivity.class);
                startActivity(mIntent);
                finish();
            }
        });

        RelativeLayout usePhotoBtn = (RelativeLayout)findViewById(R.id.usephotoBtn);
        usePhotoBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {

                final AlertDialog alertDialog = new AlertDialog.Builder(CheckResultActivity.this).create();
                alertDialog.setTitle("Enter User name");

                final EditText input = new EditText(CheckResultActivity.this);
                LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.MATCH_PARENT,
                        LinearLayout.LayoutParams.MATCH_PARENT);
                input.setLayoutParams(lp);
                alertDialog.setView(input);

                alertDialog.setButton(AlertDialog.BUTTON_NEGATIVE, "Cancel",
                        new DialogInterface.OnClickListener() {
                            public void onClick(DialogInterface dialog, int which) {
                                alertDialog.dismiss();
                            }
                        });
                alertDialog.setButton(AlertDialog.BUTTON_POSITIVE, "OK",
                        new DialogInterface.OnClickListener() {
                            public void onClick(final DialogInterface dialog, int which) {

                                progressdialog.show();
                                SharedPreferences login_prefs = getSharedPreferences("LoginInfo", MODE_PRIVATE);
                                final String user_id = login_prefs.getString("UserID", "");
                                String imagename = input.getText().toString();
                                File inputFile = new File(mFilePath);

                                RequestParams params = new RequestParams();

                                try {
                                    params.put("files[0]", inputFile, "image/jpeg");
                                    params.put("name", imagename);
                                    params.put("customerid", user_id);
                                } catch (FileNotFoundException e) {
                                    e.printStackTrace();
                                }

                                AsyncHttpClient client = new AsyncHttpClient();

                                client.post(NetworkManager.uploadPath, params, new AsyncHttpResponseHandler() {
                                    @Override
                                    public void onSuccess(int i, cz.msebera.android.httpclient.Header[] headers, byte[] bytes) {
                                        progressdialog.dismiss();

                                        SharedPreferences url_prefs = getSharedPreferences("URLInfo", MODE_PRIVATE);
                                        String return_url = url_prefs.getString("returnUrl", "");

                                        if(return_url == ""){
                                            return_url = "print/myprints";
                                        }

                                        String result_url = "/directlogin?returnurl=" + return_url + "&customerid=" + user_id;
                                        Intent mIntent = new Intent(CheckResultActivity.this, WebviewActivity.class);
                                        mIntent.putExtra("URLinfo", result_url);
                                        startActivity(mIntent);
                                    }

                                    @Override
                                    public void onFailure(int i, cz.msebera.android.httpclient.Header[] headers, byte[] bytes, Throwable throwable) {
                                        progressdialog.dismiss();

                                        AlertDialog alertDialog = new AlertDialog.Builder(CheckResultActivity.this).create();
                                        alertDialog.setTitle("Uploading Error!");
                                        alertDialog.setMessage("Please check your internet connection and try again.");
                                        alertDialog.setButton(AlertDialog.BUTTON_NEUTRAL, "OK",
                                                new DialogInterface.OnClickListener() {
                                                    public void onClick(DialogInterface dialog, int which) {
                                                        dialog.dismiss();
                                                    }
                                                });
                                        alertDialog.show();
                                    }

                                    @Override
                                    public void onProgress(long bytesWritten, long totalSize) {
                                        Log.i("xml","Progress : "+bytesWritten);
                                    }
                                });

                            }
                        });
                alertDialog.show();
            }
        });
    }
}
