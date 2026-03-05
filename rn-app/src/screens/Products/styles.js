import {StyleSheet, Dimensions, Platform} from 'react-native'

import * as Colors from '../../styles/colors'
const {width: deviceWidth, height: deviceHeight} = Dimensions.get('window');

export default StyleSheet.create({
	container: {
		flex: 1
	},
	innerContainer: {
		justifyContent: 'flex-start',
		width: deviceWidth,
	},
	header: {
		borderBottomColor: Colors.grayishBorderColor,
		borderBottomWidth: 1,
		flexDirection: 'row',
		paddingHorizontal: 18,
		paddingVertical: 20,
		alignItems: 'center'
	},
	logoWrap: {
		alignItems: 'center',
		flexGrow: 1
	},
	subheader: {
		flexDirection: 'row',
		paddingHorizontal: 18,
		justifyContent: 'space-between',
		paddingVertical: 14,
	},
	activeSubheader: {
		backgroundColor: 'rgba(135, 129, 129, 0.053252)',
	},
	subheaderTitle: {
		color: Colors.subheaderTextColor,
		fontSize: 16,
		lineHeight: 22,
		letterSpacing: -0.385882,
	},

	homeSliderWrapper: {
		width: deviceWidth,
		marginBottom:20
		// marginTop: 10
	},
	homeSlider: {
		width: deviceWidth,
		height: deviceHeight * .23,
	},
	homeSliderImageContainer: {
		flex: 1,
		marginBottom: Platform.select({ios: 0, android: 1}), // Prevent a random Android rendering issue
		backgroundColor: 'white',
		borderRadius: 8,
	},
	homeSliderImage: {
		...StyleSheet.absoluteFillObject,
		resizeMode: 'cover',
	},

	singleProductCategory: {
		textAlign: 'center',
		flexGrow: 1,
		fontFamily: 'Avenir',
		fontWeight: '800',
		fontSize: 17,
		lineHeight: 22,
		letterSpacing: -0.41,
	},
	singleProductImages: {
		borderBottomColor: Colors.grayishBorderColor,
		borderBottomWidth: 1,
		marginBottom: 25,
		paddingBottom:10
	},
	singleProductImage: {
		width: deviceWidth,
		height: deviceWidth * .5,
		alignSelf: 'center',
	},
	singleProductDescription: {
		fontFamily: 'Avenir',
		fontSize: 15,
		lineHeight: 20,
		letterSpacing: -0.24,
		margin: 15,
	},
	singleProductTitle: {
		textAlign: 'left',
		fontFamily: 'Avenir',
		fontWeight: '800',
		fontSize: 22,
		lineHeight: 28,
		letterSpacing: 0.35,
		textTransform: 'uppercase',
		color: Colors.darkColor,
		paddingHorizontal: 15
	},
	singleProductPrice: {
		textAlign: 'left',
		fontFamily: 'Avenir',
		fontSize: 22,
		lineHeight: 34,
		letterSpacing: 0.265294,
		textTransform: 'uppercase',
		color: Colors.darkColor,
		paddingHorizontal: 15
	},
	singleProductVariants: {
		marginTop: 15,
	},

	stickyFooter: {
		backgroundColor: Colors.secondaryBackgroundColor,
		position: 'absolute',
		top: deviceHeight - 97,
		left: 0,
		paddingHorizontal: 15,
		paddingVertical: 25,
		width: deviceWidth,
		flexDirection: 'row',
		height: 97,

		shadowColor: "#000",
		shadowOffset: {
		width: 0,
		height: 3,
		},
		shadowOpacity: 0.27,
		shadowRadius: 4.65,

		elevation: 6,
	},
	primaryButton: {
		backgroundColor: Colors.primaryBackgroundColor,
		borderRadius: 4,
		alignSelf: 'center',
		width: deviceWidth - 120
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
	primaryButtonText: {
		color: Colors.secondaryTextColor,
		textAlign: 'center',
		fontFamily: 'Avenir',
		fontSize: 17,
		lineHeight: 22,
		letterSpacing: -0.41,
		paddingVertical: 12
	},
	favoriteButton: {
		borderColor: Colors.primaryBackgroundColor,
		borderWidth: 1,
		borderRadius: 4,
		justifyContent: 'center',
		alignItems: 'center',
		height: 46,
		width: 77,
		marginRight: 10
	},

	productsWrap: {
		width: deviceWidth,
		flexWrap: 'wrap',
		flexDirection: 'row',
		marginHorizontal: 8
	},
	productWrap: {
		width: (deviceWidth) / 2 - 10,
		alignItems:'center',
		justifyContent:'center',
		backgroundColor: Colors.secondaryBackgroundColor,
	},
	product: {
		backgroundColor: Colors.secondaryBackgroundColor,
		borderRadius: 4,
		alignItems: 'center',
		marginBottom: 20,
		marginHorizontal: 8,
		width:'90%',
		shadowColor: Colors.darkColor,
		shadowOffset: {
			width: 0,
			height: 1,
		},
		shadowOpacity: 0.22,
		shadowRadius: 2.22,

		elevation: 2,
	},
	favoriteProduct : {
		paddingVertical:20
	},
	favoriteProductImage : {
		width: '90%',
		height: deviceWidth * 0.50,
	},
	productImage: {
		// width: ((deviceWidth - 42) / 2) - 10,
		// height: ((deviceWidth - 42) / 2) - 10,
		width: deviceWidth * 0.25,
		height: deviceWidth * 0.25,
	},
	productPrice: {
		fontFamily: 'Avenir',
		fontSize: 15,
		lineHeight: 20,
		textAlign: 'center',
		letterSpacing: -0.24,
		color: Colors.darkColor,
		marginBottom: 15
	},
	productCount: {
		fontFamily: 'Avenir',
		fontSize: 12,
		lineHeight: 20,
		textAlign: 'center',
		letterSpacing: -0.24,
		color: Colors.labelColor,
		marginBottom: 15
	},
	productFavorite: {
		position: 'absolute',
		top: 10,
		right: 10
	},
	productFulfillmentStatusView:{
		position: 'absolute',
		top: 10,
		left: 10,
		borderRadius:5,
		paddingHorizontal:10
	},
	productFulfillmentStatus: {
		// position: 'absolute',
		// top: 10,
		// left: 10,
		color: Colors.secondaryTextColor,
		fontFamily: 'Avenir',
		fontSize: 14,
		lineHeight: 20,
		// backgroundColor: Colors.yellowBackgroundColor,
		borderRadius: 6,
		paddingVertical: 2,
		paddingHorizontal: 8
	},
	productFulfilled: {
		backgroundColor: Colors.blueBackgroundColor
	},

	sortWrap: {
		width: deviceWidth,
		backgroundColor: Colors.secondaryBackgroundColor,
		position: 'absolute',
		top: 0,
	},
	sortTitle: {
		fontFamily: 'Avenir',
		fontSize: 16,
		lineHeight: 22,
		letterSpacing: -0.385882,
		color: Colors.darkColor,
		marginHorizontal: 18,
		marginVertical: 14
	},
	dropdownMenu: {
		borderColor: Colors.secondaryBackgroundColor,
		borderWidth: 1,
		borderRadius: 4,
		backgroundColor: Colors.yellowBackgroundColor,
		paddingVertical: 8,
		paddingHorizontal: 17,
		marginTop: 6,
		marginBottom: 15,
		marginHorizontal: 17
	},

	selectedPickerOptionText: {
		fontFamily: 'Avenir',
		fontSize: 17,
		lineHeight: 22,
		letterSpacing: -0.41,
		color: Colors.secondaryTextColor
	},
	pickerIcon: {
		position: 'absolute',
		top: 15,
		right: 15,
	},
	pickerModal: {
		flex: 1,
		justifyContent: 'center',
		alignItems: 'center',
	},
	pickerModalBackdrop: {
		backgroundColor: 'rgba(50, 50, 50, 0.75)',
		width: deviceWidth,
		height: deviceHeight,
		position: 'absolute',
		top: 0,
		left: 0
	},
	pickerItemsWrap: {
		backgroundColor: Colors.secondaryBackgroundColor,
		borderRadius: 12,
		width: deviceWidth * 0.9,
		alignSelf: 'center'
	},
	fingerprintsModalBackdrop: {
		flex: 1,
		backgroundColor: 'rgba(50, 50, 50, 0.75)'
	},
	fingerprintsModal: {
		position: 'absolute',
		left: 50,
		backgroundColor: Colors.secondaryBackgroundColor,
		borderRadius: 12,
		width: deviceWidth - 100,
		justifyContent: 'center',
	},
	vaultItem: {
		flexDirection: 'row',
		paddingVertical: 12,
		marginHorizontal: 20,
		borderColor: Colors.grayishBorderColor,
		borderBottomWidth: 1,
	},
	vaultItemName: {
		color: Colors.darkColor,
		textAlign: 'left',
		fontFamily: 'Avenir',
		fontSize: 17,
		lineHeight: 22,
		letterSpacing: -0.41,
	},
	fingerprintsModalTitle: {
		textAlign: 'center',
		fontSize: 22,
		padding: 15,
		marginVertical:10
	},

	sectionTitle: {
		fontFamily: 'Avenir',
		fontSize: 16,
		lineHeight: 22,
		letterSpacing: -0.385882,
		color: Colors.darkColor,
		marginHorizontal: 18,
		marginVertical: 24
	},
	buttonsRow: {
		flexDirection: 'column',
		paddingHorizontal: 25,
		paddingBottom: 25
	},
	secondaryButton: {
		backgroundColor: Colors.secondaryBackgroundColor,
		borderColor: Colors.primaryBackgroundColor,
		borderWidth: 1,
		borderRadius: 4,
		marginHorizontal: 10,
		marginBottom: 15,
		width : deviceWidth - 120
	},
	secondaryButtonText: {
		color: Colors.primaryBackgroundColor,
		textAlign: 'center',
		fontFamily: 'Avenir',
		fontSize: 17,
		lineHeight: 22,
		letterSpacing: -0.41,
		paddingVertical: 12,
		fontWeight: '800',
	},

	applyButton: {
		alignSelf: 'flex-end',
		marginHorizontal: 30,
		marginVertical: 22
	},
	applyButtonText: {
		color: Colors.primaryColor,
		fontFamily: 'Avenir',
		fontSize: 16,
		lineHeight: 22,
	},
	sideMenuApplyButton: {
		backgroundColor: Colors.secondaryBackgroundColor,
		borderRadius: 6,
		padding: 8
	},
	sideMenuApplyButtonText: {
		fontWeight: 'bold'
	},

	sidemenuWrap: {
		position: 'absolute',
		left: 0,
		top: 0,
		width: deviceWidth - 50,
		height: deviceHeight,
		backgroundColor: Colors.yellowBackgroundColor,
		paddingHorizontal: 17,
		paddingTop: 90,
		flex: 1
	},
	priceRangeWrap: {
		marginHorizontal: 20,
		marginVertical: 20,
	},
	sidemenuPickerTitle: {
		fontFamily: 'Avenir',
		color: Colors.secondaryTextColor,
		paddingLeft: 18,
		fontWeight: '500',
		fontSize: (Platform.OS == 'ios') ? 17 : 20, 
		lineHeight: 22,
		marginTop:(Platform.OS == 'ios') ? 0 : 20,
		letterSpacing: -0.41,
	},
	checkoutDetail: {
		textAlign: 'left',
		fontFamily: 'Avenir',
		fontSize: 17,
		lineHeight: 22,
		letterSpacing: 0.265294,
		color: Colors.darkColor,
		paddingHorizontal: 15
	},
	webview: {
		flex: 1,
		width: deviceWidth,
	},
	noRecordFound: {
		textAlign: 'center',
		flexGrow: 1,
		fontFamily: 'Avenir',
		fontWeight: '800',
		fontSize: 17,
		lineHeight: 22,
		letterSpacing: -0.41,
	},
	myOrderProjectImage : {
		width: deviceWidth * 0.40,
		height: deviceWidth * 0.50,
		marginVertical: deviceWidth * 0.02,
		marginTop: 30
	},
	noRecordFoundView:{
		alignItems:'center', justifyContent:'center', flex:1
	},
	noRecordText: {
		color: Colors.darkColor,
		textAlign:'center',
		alignSelf:'center',
		fontSize: 18,
		lineHeight: 22,
		letterSpacing: -0.385882,
	},
});