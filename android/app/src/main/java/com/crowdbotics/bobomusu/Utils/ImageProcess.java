package com.crowdbotics.bobomusu.Utils;

import android.content.res.Resources;
import android.graphics.Bitmap;
import org.opencv.android.Utils;
import org.opencv.core.Core;
import org.opencv.core.CvType;
import org.opencv.core.Mat;
import org.opencv.core.Point;
import org.opencv.core.Rect;
import org.opencv.core.Scalar;
import org.opencv.core.Size;
import org.opencv.imgproc.Imgproc;

public class ImageProcess {

    int screenwid;
    int screenhei;

    public ImageProcess(int wid, int hei){
        this.screenwid = wid;
        this.screenhei = hei;
    }

    public Bitmap getFingerImage(Bitmap inputImg)
    {
        //convert bitmap to mat
        Mat inputMat = new Mat();
        Utils.bitmapToMat(inputImg, inputMat);

        //get cropping rect info
        int cropwid = dpToPx(160);
        int crophei = dpToPx(160);
        double ratiox = (double)cropwid / screenwid;
        double ratioy = (double)crophei / screenhei;
        int rectWid = (int)(inputMat.width() * ratiox);
        int rectHei = (int)(inputMat.height() * ratioy);
        int leftx = (int)((inputMat.width() - (double)rectWid) / 2);
        int lefty = (int)((inputMat.height() - (double)rectHei) / 2);

        //crop the mat with rectangle
        Mat cropMat = new Mat(inputMat, new Rect(leftx, lefty, rectWid, rectHei));
        //resize the Mat for processing
        double percentage = 600.0 / (rectWid);
        double new_height = rectHei * percentage;
        Size new_size = new Size(600.0, new_height);
        Imgproc.resize(cropMat, cropMat, new_size);

        //preprocess the image
        Imgproc.cvtColor(cropMat, cropMat, Imgproc.COLOR_BGR2GRAY);
        Imgproc.equalizeHist(cropMat, cropMat);
        Imgproc.GaussianBlur(cropMat,cropMat, new Size(3,3),0 );

        //get binary Image
        Imgproc.adaptiveThreshold(cropMat, cropMat, 255,
                Imgproc.ADAPTIVE_THRESH_GAUSSIAN_C,
                Imgproc.THRESH_BINARY,
                17, 3);
        Imgproc.medianBlur(cropMat, cropMat, 3);

        Mat mask = new Mat(cropMat.height(), cropMat.width(), CvType.CV_8UC1, new Scalar(0,0,0));
        Imgproc.ellipse(mask, new Point(300, new_height / 2.0), new Size(cropMat.width() * 0.35, cropMat.height() * 0.32), 0, 0, 360, new Scalar(255, 255, 255), -1, 8,0);

        Mat result =  new Mat();
        Core.bitwise_and(cropMat, mask, result);

        Imgproc.cvtColor(cropMat, cropMat, Imgproc.COLOR_GRAY2BGR);
        Mat foreground = new Mat(result.size(), CvType.CV_8UC3, new Scalar(255,
                255, 255,255));
        cropMat.copyTo(foreground ,mask);

        //convert mat to bitmap
        Bitmap bmp = Bitmap.createBitmap(foreground.cols(), foreground.rows(),
                Bitmap.Config.ARGB_8888);
        Utils.matToBitmap(foreground,bmp);

        return bmp;
    }

    public static int dpToPx(int dp)
    {
        return (int) (dp * Resources.getSystem().getDisplayMetrics().density);
    }
}
