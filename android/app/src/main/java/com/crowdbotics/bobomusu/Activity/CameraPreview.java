package com.crowdbotics.bobomusu.Activity;

import android.content.Context;
import android.hardware.Camera;
import android.util.Log;
import android.view.SurfaceHolder;
import android.view.SurfaceView;

import java.util.List;

public class CameraPreview extends SurfaceView implements SurfaceHolder.Callback {

    private SurfaceHolder mHolder;
    private Camera mCamera;
    private static final String TAG = "CameraScan";
    public Camera.Size mDefaultSize;
    private Camera.Size mPictureSize;

    public CameraPreview(Context context, Camera camera) {
        super(context);

        mCamera = camera;
        mHolder = getHolder();
        mHolder.addCallback(this);
        mHolder.setType(SurfaceHolder.SURFACE_TYPE_PUSH_BUFFERS);
    }

    public void surfaceCreated(SurfaceHolder holder) {
        if(mCamera == null){
            return;
        }

        try {
            mCamera.setPreviewDisplay(holder);
            mCamera.startPreview();
        } catch (Exception e) {
            e.printStackTrace();
            Log.d(TAG, "Error setting camera preview: " + e.getMessage());
        }
    }

    public void surfaceDestroyed(SurfaceHolder holder) { }

    public void surfaceChanged(SurfaceHolder holder, int format, int w, int h) {

        if (mHolder.getSurface() == null){
            return;
        }

        try {
            mCamera.stopPreview();
        } catch (Exception e){
            e.printStackTrace();
        }

        Camera.Parameters parameters = mCamera.getParameters();
        mCamera.setDisplayOrientation(90);

        mDefaultSize = getOptimalPreviewSize();
        parameters.setPreviewSize(mDefaultSize.width, mDefaultSize.height);
        parameters.setExposureCompensation(1);

        if (null == mCamera) {
            return;
        }
        List<String> focusModes = parameters.getSupportedFocusModes();

        if (focusModes.contains(Camera.Parameters.FOCUS_MODE_CONTINUOUS_PICTURE)) {
            parameters.setFocusMode(Camera.Parameters.FOCUS_MODE_CONTINUOUS_PICTURE);
        }
        else if (focusModes.contains(Camera.Parameters.FOCUS_MODE_AUTO)) {
            parameters.setFocusMode(Camera.Parameters.FOCUS_MODE_AUTO);
        }
        else if (focusModes.contains(Camera.Parameters.FOCUS_MODE_CONTINUOUS_VIDEO)){
            parameters.setFocusMode(Camera.Parameters.FOCUS_MODE_CONTINUOUS_VIDEO);
        }
        else {
            parameters.setFocusMode(Camera.Parameters.FOCUS_MODE_FIXED);
        }

        mPictureSize = getOptimalPictureSize();
        parameters.setPictureSize(mPictureSize.width, mPictureSize.height);
        mCamera.setParameters(parameters);

        try {
            mCamera.setPreviewDisplay(mHolder);
            mCamera.startPreview();

        } catch (Exception e){
            Log.d(TAG, "Error starting camera preview: " + e.getMessage());
        }
    }

    public Camera.Size getOptimalPreviewSize(){
        Camera.Parameters parameters = mCamera.getParameters();
        List<Camera.Size> sizes = parameters.getSupportedPreviewSizes();
        Camera.Size optimalsize = null;

        int[] temp = new int[sizes.size()];
        for (int i = 0; i < sizes.size(); i++){
            temp[i] = sizes.get(i).width + sizes.get(i).height;
        }

        for (int i = 0; i < sizes.size(); i++){
            if(sizes.get(i).width + sizes.get(i).height == getMax(temp)){
                optimalsize = sizes.get(i);
            }
        }

        Log.i(TAG, "Available PreviewSize: "+optimalsize.width+" "+optimalsize.height);
        return optimalsize;
    }

    public Camera.Size getOptimalPictureSize(){
        Camera.Parameters parameters = mCamera.getParameters();
        List<Camera.Size> sizes = parameters.getSupportedPictureSizes();
        Camera.Size optimalsize = null;

        int[] temp = new int[sizes.size()];
        for (int i = 0; i < sizes.size(); i++){
            temp[i] = sizes.get(i).width + sizes.get(i).height;
        }

        for (int i = 0; i < sizes.size(); i++){
            if(sizes.get(i).width + sizes.get(i).height == getMax(temp)){
                optimalsize = sizes.get(i);
            }
        }

        Log.i(TAG, "Available PreviewSize: "+optimalsize.width+" "+optimalsize.height);
        return optimalsize;
    }

    public static int getMax(int[] inputArray){
        int maxValue = inputArray[0];
        for(int i=1;i < inputArray.length;i++){
            if(inputArray[i] > maxValue){
                maxValue = inputArray[i];
            }
        }
        return maxValue;
    }
}
