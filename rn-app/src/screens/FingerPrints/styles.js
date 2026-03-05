import {StyleSheet, Dimensions, Platform} from 'react-native';
import globalVar from '../../constants/globalVar';

import * as Colors from '../../styles/colors';
const {width: deviceWidth, height: deviceHeight} = Dimensions.get('window');

export default StyleSheet.create({
  container: {
    flex: 1,
  },
  innerContainer: {
    flex: 1,
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    paddingHorizontal: 18,
    paddingVertical: 20,
    alignItems: 'center',
    width: deviceWidth
  },
  title: {
    textAlign: 'center',
    flexGrow: 1,
    fontFamily: 'Avenir',
    fontWeight: '800',
    fontSize: 17,
    lineHeight: 22,
    letterSpacing: -0.41,
  },

  requestFPNotice: {
    fontFamily: 'Avenir',
    fontSize: 22,
    lineHeight: 28,
    marginVertical: 20
  },
  buttonsWrap: {
    paddingHorizontal: 25,
    marginTop: 10,
    marginBottom: 26,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%'
  },
  heading: {
    // textShadowColor: '#9B9B9B',
    // textShadowOffset: {width: 0, height: 2},
    textShadowRadius: 4,
    textAlign: 'center',
    fontFamily: 'Avenir',
    fontWeight: 'bold',
    fontSize: 18,
    // lineHeight: 28,
    color: Colors.darkColor,
    paddingHorizontal: 20,
    marginVertical:20
    // marginBottom: 70
  },
  sidemenuWrap: {
    position: 'absolute',
    left: 0,
    top: 0,
    width: deviceWidth,
    height: deviceHeight,
    backgroundColor: Colors.transparent,
    zIndex : 1,
    elevation:3
  },
  subSidemenuWrap: {
    backgroundColor: Colors.secondaryTextColor,
    width: deviceWidth - 75,
    height: deviceHeight,
  },
  sidemenuHeader:{
    marginTop:50, flexDirection:'row', alignItems:'center', justifyContent:'center', paddingHorizontal:10
  },
  dismissSidemenuButton: {
    backgroundColor: Colors.goldishBackgroundColor,
    alignItems: 'center',
    justifyContent: 'center',
    borderTopRightRadius: 4,
    borderBottomRightRadius: 4,
    padding: 0
  },

  sidemenuTitle: {
    fontFamily: 'Avenir',
    fontWeight: '800',
    fontSize: 24,
    lineHeight: 34,
    letterSpacing: 0.337,
    color: Colors.darkColor,
    paddingHorizontal: 30,
  },
  tutorialSteps: {
    fontFamily: 'Avenir',
    fontSize: 14,
    lineHeight: 22,
    color: Colors.darkColor,
    // textShadowColor: '#D8D8D8',
    // textShadowOffset: {width: 0, height: 2},
    // textShadowRadius: 4,
    paddingHorizontal: 30,
    marginBottom: 22
  },
  sidemenuNoticeTitle: {
    fontFamily: 'Avenir',
    fontWeight: '800',
    fontSize: 22,
    lineHeight: 28,
    letterSpacing: 0.35,
    color: Colors.secondaryTextColor,
    textShadowColor: '#D8D8D8',
    textShadowOffset: {width: 0, height: 2},
    textShadowRadius: 4,
    paddingHorizontal: 30,
    marginTop: 22,
  },
  sidemenuButton: {
    borderWidth: 1,
    borderColor: Colors.secondaryTextColor,
    borderRadius: 4,
    paddingVertical: 12,
    marginHorizontal: 30,
    marginTop: 70
  },
  sidemenuButtonText: {
    color: Colors.secondaryTextColor,
    fontFamily: 'Avenir',
    fontWeight: '800',
    fontSize: 17,
    lineHeight: 22,
    letterSpacing: 0.41,
    textAlign: 'center',
  },

  fpPreviewTitle: {
    color: Colors.darkColor,
    fontFamily: 'Avenir',
    fontWeight: '800',
    fontSize: 16,
    lineHeight: 20,
    // letterSpacing: 0.33,
    // padding: 30,
    width: deviceWidth,
    textAlign:'center'
  },
  fpPreviewSubtitle: {
    color: Colors.darkColor,
    fontFamily: 'Avenir',
    fontSize: 22,
    lineHeight: 34,
    letterSpacing: 0.26,
    marginLeft: 20,
    marginBottom: 16,
    marginTop: 10,
    alignSelf: 'flex-start',
    fontWeight :'bold'

  },
  takenPhotoWrap: {
    borderWidth: 1,
    borderColor: Colors.secondaryTextColor,
    width: deviceWidth
  },
  takenPhoto: {
    width: deviceWidth / 2 - 40,
    height: deviceWidth / 2 - 40,
    // marginRight:-5
  },
  previewTakenPhoto: {
    width: deviceWidth * .7,
    height: deviceWidth * .7
  },
  zoomInIcon: {
    position: 'absolute',
    right: 50,
    top: 10
  },
  backButtonWrap: {
    marginHorizontal: 15
  },

  primaryButton: {
    backgroundColor: Colors.primaryBackgroundColor,
    borderRadius: 4,
    alignSelf: 'center',
    width: deviceWidth - 120,
    marginTop: 40,
    marginBottom: 17
  },
  
  secondaryButton: {
    backgroundColor: Colors.secondaryBackgroundColor,
    borderColor: Colors.primaryBackgroundColor,
    borderRadius: 4,
    borderWidth: 1,
    alignSelf: 'center',
    width: deviceWidth - 120,
  },
  buttonText: {
    color: Colors.secondaryTextColor,
    textAlign: 'center',
    fontFamily: 'Avenir',
    fontSize: 17,
    lineHeight: 22,
    letterSpacing: -0.41,
    paddingVertical: 12
  },

  inputFieldsWrap: {
    marginHorizontal: 30,
    marginVertical: 40
  },
  inputField: {
    borderColor: Colors.primaryColor,
    borderWidth: 1,
    borderRadius: 4,
    backgroundColor: Colors.secondaryBackgroundColor,
    paddingHorizontal: 17,
    paddingVertical: 8,
    fontFamily: 'Avenir',
    fontSize: 17,
    lineHeight: 24,
    letterSpacing: -0.41,
    color: Colors.primaryTextColor,
  },
  inputFieldLabel: {
    fontFamily: 'Avenir',
    fontWeight: '300',
    fontSize: 14,
    lineHeight: 28,
    textTransform: 'uppercase',
    color: Colors.labelColor,
  },
  activityIndicatorWrap: {
    position: 'absolute',
    top: Platform.OS == 'ios' ?  (globalVar.isIphoneX) ? -45 : -20 : 30,
    left: 0,
    backgroundColor: 'rgba(150, 150, 150, 0.5)',
    width: deviceWidth,
    height: deviceHeight,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex:1
  },

  vaultItemsWrap: {
    marginTop: 20,
  },
  vaultItem: {
    flexDirection: 'row',
    paddingVertical: 12,
    marginHorizontal: 20,
    borderColor: Colors.grayishBorderColor,
    borderBottomWidth: 1,
    justifyContent:'space-between',
    alignItems:'center'
  },
  vaultItemName: {
    color: Colors.darkColor,
    textAlign: 'left',
    fontFamily: 'Avenir',
    fontSize: 17,
    lineHeight: 22,
    letterSpacing: -0.41,
  },
  vaultNotice: {
    alignSelf: 'center',
    margin: 25,

  },
  vaultNoticeText: {
    textAlign: 'center',
    color: Colors.darkColor,
    fontFamily: 'Avenir',
    fontSize: 18,
    lineHeight: 22,
    letterSpacing: -0.41,
  },

  tutorialAnimationImages: {
    width: deviceWidth * .8,
    height: deviceWidth * .8,
    alignSelf: 'center',
    marginBottom: 0,
  },
  tutorialAnimationText: {
    fontFamily: 'Avenir',
    fontStyle: 'normal',
    fontWeight: '500',
    fontSize: 20,
    lineHeight: 22,
    textAlign: 'center',
    color: Colors.darkColor,
    paddingHorizontal: 20,
    marginTop: 45
  },
  captureButton:{
    alignItems:'center',
    justifyContent:'center',
    marginBottom:50
  },
  captureButtonImage:{
    height:70, width: 70 , tintColor: Colors.primaryBackgroundColor
  },
  autoFocusBox: {
    position: 'absolute',
    height: 64,
    width: 64,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: 'white',
    opacity: 0.4,
  },
  titleText:{
    fontFamily: 'Avenir',
    fontStyle: 'normal',
    fontWeight: '500',
    fontSize: 16,
    lineHeight: 34,
    textAlign: 'center',
    color: Colors.primaryColor,
  }
});
