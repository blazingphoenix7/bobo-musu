package com.crowdbotics.bobomusu.Activity;

import android.content.Intent;
import android.os.Bundle;

import androidx.appcompat.app.AppCompatActivity;

import com.crowdbotics.bobomusu.R;

public class SplashActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_splash);

        //
        Thread myThread = new Thread(){
            @Override
            public void run(){
                try {
                    sleep(1000);
                    Intent intent = new Intent(SplashActivity.this, WebviewActivity.class);
                    startActivity(intent);
                    finish();

                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
        };

        myThread.start();
    }
}
