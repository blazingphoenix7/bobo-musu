package com.crowdbotics.bobomusu.Networking;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class WebviewClient extends WebViewClient {

    private Activity activity = null;

    public WebviewClient(Activity activity) {
        this.activity = activity;
    }

    @Override
    public boolean shouldOverrideUrlLoading(WebView webView, String url) {
        String s = Uri.parse(url).getHost();
        if (s.equals("http://ec2-18-223-107-117.us-east-2.compute.amazonaws.com/")) {
            // This is my website, so do not override; let my WebView load the page
            return false;
        }

        Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
        activity.startActivity(intent);
        return true;
    }
}
