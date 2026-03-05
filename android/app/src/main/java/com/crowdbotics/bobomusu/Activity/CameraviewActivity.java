package com.crowdbotics.bobomusu.Activity;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.Matrix;
import android.hardware.Camera;
import android.os.Environment;
import android.os.Bundle;
import android.util.DisplayMetrics;
import android.util.Log;
import android.view.Display;
import android.view.Surface;
import android.view.View;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.RelativeLayout;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import com.crowdbotics.bobomusu.R;
import com.crowdbotics.bobomusu.Utils.ImageProcess;
import com.progressbar_lib.cc.cloudist.acplibrary.ACProgressConstant;
import com.progressbar_lib.cc.cloudist.acplibrary.ACProgressFlower;

import org.opencv.android.BaseLoaderCallback;
import org.opencv.android.LoaderCallbackInterface;
import org.opencv.android.OpenCVLoader;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;

public class CameraviewActivity extends AppCompatActivity {

    private Camera mCamera;
    private CameraPreview mPreview;
    private final static String TAG = "CameraActivity";
    private ACProgressFlower dialog = null;
    private ImageProcess imageProcess;

    //OpenCv Load
    private BaseLoaderCallback mLoaderCallback = new BaseLoaderCallback(this) {
        @Override
        public void onManagerConnected(int status) {
            switch (status)
            {
                case LoaderCallbackInterface.SUCCESS:
                    Log.d(TAG, "OpenCV loaded successfully!!");
                    break;
                default:
                    break;
            }
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_cameraview);

        if (!OpenCVLoader.initDebug()) {
            Log.d("OpenCV", "Internal OpenCV library not found. Using OpenCV Manager for initialization");
            OpenCVLoader.initAsync(OpenCVLoader.OPENCV_VERSION_3_2_0, this, mLoaderCallback);
        } else {
            Log.d("OpenCV", "OpenCV library found inside package. Using it!");
            mLoaderCallback.onManagerConnected(LoaderCallbackInterface.SUCCESS);
        }

        //progress dialog init
        dialog = new ACProgressFlower.Builder(this)
                .sizeRatio(0.15f)
                .petalThickness(5)
                .direction(ACProgressConstant.DIRECT_CLOCKWISE)
                .themeColor(Color.WHITE)
                .text("")
                .fadeColor(Color.DKGRAY).build();

        //capture Button listener
        TextView captureBtn = (TextView)findViewById(R.id.captureBtn);
        captureBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                mCamera.takePicture(null, null, mPicture);
            }
        });

        // cancel Button listener
        TextView cancelBtn = (TextView)findViewById(R.id.cancelBtn);
        cancelBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                mCamera.setPreviewCallback(null);
                mCamera.stopPreview();
                mCamera.release();
                mCamera = null;
                finish();
            }
        });
    }

    //check permission for camera
    private boolean checkPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
                != PackageManager.PERMISSION_GRANTED) {
            // Permission is not granted
            return false;
        }
        return true;
    }

    @Override
    protected void onResume() {
        super.onResume();

        if (checkPermission()) {
            //add camera preview
            addCameraView();
        } else {
            String[] temp = new String[3];
            int index = 0;
            //Camera Permission
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_DENIED)
                temp[index++] = Manifest.permission.CAMERA;

            //Storage permission
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE)
                    == PackageManager.PERMISSION_DENIED)
                temp[index++] = Manifest.permission.WRITE_EXTERNAL_STORAGE;

            if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_EXTERNAL_STORAGE)
                    == PackageManager.PERMISSION_DENIED)
                temp[index++] = Manifest.permission.READ_EXTERNAL_STORAGE;


            if(index > 0) {
                ActivityCompat.requestPermissions(this, temp, 1001);
            }
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        //if activity is finished, camera will be released.
        if (isFinishing() & mCamera != null) {
            mCamera.setPreviewCallback(null);
            mCamera.stopPreview();
            mCamera.release();
            mCamera = null;
        }
    }

    //Camera open
    private void addCameraView() {
        if(mCamera == null)
            mCamera = getCameraInstance();
        if (mPreview == null)
        {
            mPreview = new CameraPreview(CameraviewActivity.this, mCamera);
        }

        Camera.Parameters parameters = mCamera.getParameters();
        parameters.setFlashMode(Camera.Parameters.FLASH_MODE_TORCH);
        mCamera.setParameters(parameters);

        //camera preview add to view
        final FrameLayout preview = (FrameLayout) findViewById(R.id.camera_preview);
        Camera.Size size = mPreview.getOptimalPreviewSize();
        float ratio = (float)size.width/size.height;

        DisplayMetrics displayMetrics = new DisplayMetrics();
        getWindowManager().getDefaultDisplay().getMetrics(displayMetrics);
        int screenhei = displayMetrics.heightPixels;
        int screenWid = displayMetrics.widthPixels;

        int new_width=0, new_height=0;
        if(screenWid/screenhei<ratio){
            new_width = Math.round(screenWid*ratio);
            new_height = screenWid;
        }else{
            new_width = screenWid;
            new_height = Math.round(screenWid/ratio);
        }

        RelativeLayout.LayoutParams param = (RelativeLayout.LayoutParams)preview.getLayoutParams();
        param.width = new_height;
        param.height = new_width;
        preview.setLayoutParams(param);
        preview.addView(mPreview);

        imageProcess = new ImageProcess(screenWid, screenhei);
    }

    //Camera init
    public Camera getCameraInstance(){
        if(mCamera != null)
            return mCamera;
        Camera c = null;
        try {
            c = Camera.open();
        }
        catch (Exception e){
            e.printStackTrace();
        }
        return c;
    }

    public Camera.PictureCallback mPicture = new Camera.PictureCallback() {

        @Override
        public void onPictureTaken(final byte[] data, Camera camera) {

            final File pictureFile = getOutputMediaFile();
            final String mFilePath = pictureFile.getAbsolutePath();

            if (pictureFile == null) {
                Log.d(TAG, "Error creating media file, check storage permissions: ");
                return;
            }

            new Thread(new Runnable() {
                @Override
                public void run()
                {
                    try
                    {
                        FileOutputStream fos = new FileOutputStream(pictureFile);
                        Bitmap bitmapPicture = BitmapFactory.decodeByteArray(data, 0, data.length);

                        mCamera.stopPreview();
                        mCamera.release();
                        mCamera = null;

                        runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                dialog.show();
                            }
                        });

                        final android.hardware.Camera.CameraInfo info = new android.hardware.Camera.CameraInfo();
                        Bitmap bitmap = fixBitmapOrientation(rotateImage(bitmapPicture, info.orientation));

                        Bitmap result = imageProcess.getFingerImage(bitmap);
                        result = rotate(result,90);
                        result.compress(Bitmap.CompressFormat.PNG, 100, fos);
                        fos.close();

                    } catch (FileNotFoundException e) {
                        Log.d(TAG, "File not found: " + e.getMessage());
                    } catch (IOException e) {
                        Log.d(TAG, "Error accessing file: " + e.getMessage());
                    }

                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {

                            dialog.dismiss();
                            Intent mIntent = new Intent(CameraviewActivity.this, CheckResultActivity.class);
                            mIntent.putExtra("image_path", mFilePath);
                            startActivity(mIntent);
                            finish();

                        }
                    });
                }
            }).start();
        }
    };

    private static Bitmap rotateImage(Bitmap img, int degree) {
        Matrix matrix = new Matrix();
        Bitmap rotatedImg;
        if(degree != 90) {
            matrix.postRotate(degree - 90);
            rotatedImg = Bitmap.createBitmap(img, 0, 0, img.getWidth(), img.getHeight(), matrix, true);
            img.recycle();
        } else {
            rotatedImg = img;
        }
        return rotatedImg;
    }

    private Bitmap fixBitmapOrientation(Bitmap bitmap) {
        Display display = ((WindowManager)getSystemService(WINDOW_SERVICE)).getDefaultDisplay();
        if(display.getRotation() == Surface.ROTATION_90)
            return bitmap;

        Matrix matrix = new Matrix();
        if(display.getRotation() == Surface.ROTATION_270)
            matrix.postRotate(180);

        Bitmap rotatedBitmap = Bitmap.createBitmap(bitmap, 0, 0, bitmap.getWidth(), bitmap.getHeight(), matrix, true);
        return rotatedBitmap;
    }

    private  File getOutputMediaFile(){
        File mediaStorageDir = new File(Environment.getExternalStoragePublicDirectory(
                Environment.DIRECTORY_PICTURES), "Bobo&Musu");

        if (! mediaStorageDir.exists()){
            if (! mediaStorageDir.mkdirs()){
                return null;
            }
        }

        String timeStamp = new SimpleDateFormat("ddMM_HHmmss").format(new Date());
        File mediaFile;
        String mImageName="MI_"+ timeStamp +".jpg";
        mediaFile = new File(mediaStorageDir.getPath() + File.separator + mImageName);
        return mediaFile;
    }

    public static Bitmap rotate(Bitmap bitmap, int degree) {
        int w = bitmap.getWidth();
        int h = bitmap.getHeight();

        Matrix mtx = new Matrix();
        mtx.setRotate(degree);

        return Bitmap.createBitmap(bitmap, 0, 0, w, h, mtx, true);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {

        if(requestCode == 1001) {
            for (int i = 0; i < permissions.length; i++) {
                String permission = permissions[i];
                int grantResult = grantResults[i];

                if (permission.equals(Manifest.permission.CAMERA)) {
                    if (grantResult == PackageManager.PERMISSION_GRANTED) {
                        Log.d("CAMERA","Permission Success");
                    }
                }

                if (permission.equals(Manifest.permission.WRITE_EXTERNAL_STORAGE)) {
                    if (grantResult == PackageManager.PERMISSION_GRANTED) {
                        Log.d("WRITE","SUCCESS");
                    }
                }

                if (permission.equals(Manifest.permission.READ_EXTERNAL_STORAGE)) {
                    if (grantResult == PackageManager.PERMISSION_GRANTED) {
                        Log.d("READ","SUCCESS");
                    }
                }
            }
        }

        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
    }
}
