import {StyleSheet, Dimensions, Platform} from 'react-native'
import { color } from 'react-native-reanimated'
import * as Colors from '../../styles/colors'

const {width: deviceWidth, height: deviceHeight} = Dimensions.get('window')

export default StyleSheet.create({
	container: {
		flex: 1,
	},
	innerContainer: {
		flex: 1,
		justifyContent: 'center',
		width: deviceWidth,
	},
	logo: {
		alignSelf: 'center',
		marginVertical: 30
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
	},
	
	checkboxWrap: {
		marginLeft: 15,
		flexDirection: 'row',
		alignItems: 'center',
	},
	checkboxText: {
		fontFamily: 'Avenir',
		fontSize: 14,
		lineHeight: 36,
		color: Colors.primaryTextColor,
		marginLeft: 6
	},

	primaryButton: {
		backgroundColor: Colors.primaryBackgroundColor,
		textAlign: 'center',
		borderRadius: 5,
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
	forgotPassword: {
		fontFamily: 'Avenir',
		fontStyle: 'normal',
		fontWeight: 'normal',
		fontSize: 17,
		lineHeight: 24,
		textAlign: 'center',
		color: '#000000',
		marginTop: 10,
		marginBottom: 10
	},
	// skipButton: {
	//   fontFamily: 'Avenir',
	//   fontStyle: 'normal',
	//   fontWeight: 'normal',
	//   fontSize: 17,
	//   lineHeight: 24,
	//   textAlign: 'center',
	//   color: '#000000',
	//   marginTop: 22,
	//   marginBottom: 10
	// },
	skipButton: {
		backgroundColor: Colors.secondaryBackgroundColor,
		borderWidth: 1,
		borderColor: Colors.primaryColor,
		textAlign: 'center',
		marginHorizontal: 30,
		borderRadius: 5
	},
	skipButtonText: {
		color: Colors.primaryColor,
		textAlign: 'center',
		fontFamily: 'Avenir',
		fontSize: 17,
		lineHeight: 22,
		letterSpacing: -0.41,
		paddingVertical: 12,
		fontWeight: 'bold'
	},

	header: {
		flexDirection: 'row',
		paddingHorizontal: 20,
		paddingVertical: 14,
		marginBottom: 36
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

	footer: {
		marginVertical: 15,
		width: deviceWidth,
		justifyContent: 'center'
	},
	footerTitle: {
		fontFamily: 'Avenir',
		fontSize: 17,
		lineHeight: 20,
		textAlign: 'center',
		color: 'rgba(0, 0, 0, 0.87)',
		fontWeight: '300',
		marginBottom: 8
	},
	footerSubtitle: {
		fontFamily: 'Avenir',
		fontSize: 17,
		lineHeight: 20,
		textAlign: 'center',
		textDecorationLine: 'underline',
		color: 'rgba(0, 0, 0, 0.87)',
		fontWeight : 'bold'
	},
	notice: {
		marginHorizontal: 16,
		marginBottom: 32,
		fontFamily: 'Avenir',
		fontSize: 15,
		lineHeight: 20,
		letterSpacing: -0.24,
		color: '#000'
	},

	skipText: {
		textAlign: 'center',
		fontFamily: 'Avenir',
		fontSize: 18,
		lineHeight: 28,
		color: Colors.primaryTextColor,
		marginHorizontal: 50
	},

	welcomeMiddleContainer:{
		flex:1,justifyContent:'center', alignItems:'center'
	},
	welcomeImage: {
		height:deviceHeight * .28, 
		width: deviceWidth * .4,
		marginVertical:15,
	},
	paginationStyle:{
		marginBottom: (Platform.OS == 'android') ? deviceHeight * .065 : deviceHeight * .075
	},
	dotStyle:{
		backgroundColor: Colors.secondaryBackgroundColor,
		borderWidth: StyleSheet.hairlineWidth,
		borderColor :Colors.labelColor,
		marginRight: 5,
		marginLeft: 5
	},
	activeDotStyle:{
		backgroundColor: Colors.subheaderTextColor,
		marginRight: 5,
		marginLeft: 5
	},
	welcomeSlider:{
		marginVertical:10,
		maxHeight:deviceHeight * .52
	},  
	welcomeTitle:{
		textAlign:'center',
		fontWeight:'bold',
		fontSize: 20,
		color: Colors.labelColor,
		fontFamily: 'Avenir',
	},
	welcomeDescription:{
		textAlign:'center',
		fontSize: 13,
		color: Colors.labelColor,
		textAlignVertical:'auto',
		fontFamily: 'Avenir',
		fontWeight:'700'
	},
	continueAsGuestButtonText:{
		color: Colors.primaryBackgroundColor,    
	},
	continueAsGuestButton:{
		borderColor: Colors.primaryBackgroundColor,
		marginTop:15, 
		marginHorizontal:40
	},
	countryCodeView:{
		position:'absolute', height:40, zIndex:1, bottom: (Platform.OS == 'ios') ? 0 : 5, alignItems:'center', justifyContent:'center',paddingLeft:5,
	
	}
})
