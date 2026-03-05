import {StyleSheet, Dimensions} from 'react-native'
import * as Colors from '../../styles/colors'

const {width: deviceWidth} = Dimensions.get('window')

export default StyleSheet.create({
  container: {
    flex: 1,
  },
  innerContainer: {
    flex: 1,
    justifyContent: 'flex-start',
    width: deviceWidth,
  },
  header: {
    flexDirection: 'row',
    paddingHorizontal: 20,
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
  backButtonWrap: {
    marginHorizontal: 15
  },

  inputFieldsWrap: {
    marginHorizontal: 30,
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
  mobileInputField: {
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
    width:'100%',
		paddingLeft: 85
  },
  inputFieldLabel: {
    fontFamily: 'Avenir',
    fontWeight: '300',
    fontSize: 14,
    lineHeight: 28,
    textTransform: 'uppercase',
    color: Colors.labelColor,
    marginTop: 20
  },
  
  primaryButton: {
    backgroundColor: Colors.primaryBackgroundColor,
    borderRadius: 4,
    marginTop: 75,
    alignSelf: 'center',
    width: deviceWidth - 120
  },
  primaryButtonText: {
    color: Colors.secondaryTextColor,
    textAlign: 'center',
    fontFamily: 'Avenir',
    fontSize: 17,
    lineHeight: 22,
    letterSpacing: -0.41,
    paddingVertical: 12,
    fontWeight:'bold'
  },
  countryCodeView:{
		position:'absolute', height:40, zIndex:1, bottom: (Platform.OS == 'ios') ? 0 : 5, alignItems:'center', justifyContent:'center',paddingLeft:5,
	
	}
})
