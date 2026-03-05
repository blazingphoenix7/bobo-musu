import React, {Component} from 'react';
import {
  SafeAreaView, Image, ScrollView, View, Text,
  TouchableOpacity, TouchableWithoutFeedback,
  ActivityIndicator, Modal, Alert, Dimensions
} from 'react-native';
import {Picker} from '@react-native-community/picker';
import {SliderBox} from "react-native-image-slider-box";
import {connect} from 'react-redux';
import AsyncStorage from '@react-native-community/async-storage';

import _Header from '../../components/_Header';

import styles from './styles';
import * as Colors from '../../styles/colors';
import {BackArrowIcon, HeartSolidIcon, HeartHollowIcon} from "../../components/icons";
import {selectProductAttributes, addToFavoritedProducts, removeFromFavoritedProducts} from '../../actions/products';
import {loadFingerPrints, setActiveFingerprintId} from '../../actions/fingerprints';
import { setCheckOutId, setCartCount, setCheckOutIdInServer, checkoutCustomerAssociate } from '../../actions/orders';
import {capitalizeString} from '../../helpers';
import { Container, Content, Card, Icon } from 'native-base';
import { filter } from 'lodash';
import _  from 'lodash';
import client from '../../config/shophify';

// import Modal from 'react-native-modal';

let filteringOptions = {};
const {height: deviceHeight, width: deviceWidth} = Dimensions.get('window');
let _this = null
class ConfirmationProduct extends Component {

	constructor(props){
		super(props);
		_this = this;
		const { assignPrint } = props.products;
		this.state = {
			filtering: _.get(props,'products.productVariants') || {},
			activeModal: null,
			showFingerprintsModal: false,
			fingerprintsModalHeight: 0,
			price : undefined,
			isNextButtonDisable : true,
			isModalVisible : false,
			assignPrint : assignPrint,
			isNextButton : false,
			isAddToCard : true,
			loading: false
		}
		console.log("productVariants-->", JSON.stringify(props.products))
	}

	// static getDerivedStateFromProps(props, state){
	// 	console.log('state.assignPrint.id',state.assignPrint.id)
	// 	console.log('props.products.assignPrint',props.products.assignPrint.id)
		
	// }

	componentDidUpdate(prevProps){
		// console.log('componentDidUpdate')
		const { assignPrint } = this.props.products;
		if (assignPrint.id !== this.state.assignPrint.id) {
			this.setState({
				assignPrint : this.props.products.assignPrint
			},() =>{
				this.getProductMetafields();
			});
		}
	}

	togglePickerModal = modal => this.setState({activeModal: modal});
	toggleFingerprintsModal = modal => this.setState({showFingerprintsModal: modal});
	requestPrint = () => this.props.navigation.navigate('RequestFingerPrint');

	takePrint = async () => {
		const skipTutorial = await AsyncStorage.getItem('skipTutorial');

		if(!!skipTutorial){
			this.props.navigation.navigate('TakeFingerPrint', {backToScreen: 'Product'});
		}else{
			this.props.navigation.navigate('Tutorial', {backToScreen: 'Product'});
		}
	}

	selectFingerprint = fingerprintId => {
		this.props.setActiveFingerprintId(fingerprintId);
		this.toggleFingerprintsModal(false);
	}

	handlePickerChange = (itemValue, pickerKey) => {
		console.log('pickerKey-->',pickerKey);
		console.log('itemValue-->',itemValue);
		const {activeModal} = this.state;
		console.log('activeModal-->',activeModal);
		this.props.selectProductAttributes(pickerKey, itemValue);
		let isNextButton = false
		if(pickerKey == "finger_print" && itemValue =="Take a Print" || itemValue =="Choose a Print"){
			isNextButton = true
		}

		this.setState(state => {
			state.filtering[pickerKey] = itemValue !== 'Select '+pickerKey ? itemValue : null;
			state.activeModal = null;
			state.isNextButton = isNextButton;
			return state;
		},() => {
			console.log('filtering-->',JSON.stringify(this.state.filtering));
			this.updatePriceData()
		});
	}

	updatePriceData = () => {
		const { assignPrint } = this.props.products;
		let isNextButtonDisable = false
			for(let filterValue in this.state.filtering){
				console.log('filterValue',filterValue);
				console.log('filterValue-->',this.state.filtering[filterValue]);
				if(this.state.filtering[filterValue] == null){
					isNextButtonDisable = true;
					break;
				}else{
					isNextButtonDisable = false;
				}
			}

			if(this.state.filtering.finger_print != assignPrint.fingerprint_title){
				this.setState({
					isAddToCard : false
				})
			}
			
			const product = this.props.products.activeProduct;
			let isFoundValue = false;
			
			product.variants.map((item) => {
				if(!isFoundValue){
					let isSubValueFound = [];
					item.selectedOptions.map((subItem) => {
						if(JSON.stringify(subItem.value) === JSON.stringify(this.state.filtering[subItem.name])) {
							// console.log('subItem.value', subItem.value);
							// console.log('this.state.filtering[subItem.name]', this.state.filtering[subItem.name]);
							isSubValueFound.push(true);
						}else{
							isSubValueFound.push(false);
						}
					});

					if(isSubValueFound.find(x => x == false) == undefined){
						isFoundValue = true;
						console.log('item.price', item.price);
						this.setState({
							price : item.price,
							isNextButtonDisable
						})
					}else{
						isFoundValue = false;
						this.setState({
							price : '',
							isNextButtonDisable
						})
					}
				}
			})
	}

	toggleProductFavorite = productId => {
		const customerId = this.props.user.customerDetails.id;

		if(this.isFovoriteProduct(productId)){
			this.props.removeFromFavoritedProducts(customerId, productId);
		}else{
			this.props.addToFavoritedProducts(customerId, productId);
		}
	}

	isFovoriteProduct = productId => {
		const {favoritedProducts} = this.props.products;

		for(let product of favoritedProducts){
			if(product.graphql_product_id === productId){
				return true;
			}
		}
		return false;
	}

	// proceedToCheckout = () => {
	// 	const { activeFingerprintId } = this.props.fingerprints;
	// 	const { filtering } = this.state;

	// 	console.log("filtering-->", filtering.finger_print.toLowerCase());
	// 	switch (filtering.finger_print.toLowerCase()) {
	// 		case 'take a print':

	// 			this.takePrint()
	// 			break;
	// 		case 'choose a print':
	// 			// this.toggleFingerprintsModal(true)
	// 			this.props.navigation.navigate('FingerPrintVault', {from: 'Product'})
	// 			break;
	// 		case 'request a print':
	// 			this.requestPrint()
	// 			break;	
	// 		default:
	// 			break;
	// 	}
		
	// 	return;
	// 	if(!!activeFingerprintId){
	// 		this.props.navigation.navigate('Checkout');
	// 	}else{
	// 		Alert.alert('A finger print is required', 'Please select a finger print to continue.');
	// 	}
	// }

	renderPicker = activeModal => {
		const selectedValue = this.state.filtering[activeModal];
		const options = filteringOptions[activeModal].options;

		if(Platform.OS === 'ios'){
			return (
				<Picker
					style={Platform.OS === 'ios' ? styles.pickerItemsWrap : {}}
					mode="dialog"
					selectedValue={selectedValue || '-'}
					onValueChange={(itemValue, itemIndex) => this.handlePickerChange(itemValue, activeModal)}
				>
					{options.map(option => <Picker.Item key={option} label={capitalizeString(option.replace('_and_', ' & '))} value={option} />)}
				</Picker>
			);
		}else{
			return (
				<View style={{borderWidth:1, marginHorizontal:10, marginTop:5}}> 
					<Picker
						enabled={activeModal != 'finger_print'}
						style={Platform.OS === 'ios' ? styles.pickerItemsWrap : {}}
						mode="dialog"
						selectedValue={selectedValue || '-'}
						onValueChange={(itemValue, itemIndex) => this.handlePickerChange(itemValue, activeModal)}
					>
						{options.map(option => <Picker.Item key={option} label={capitalizeString(option.replace('_and_', ' & '))} value={option} />)}
					</Picker>
				</View>
			);
		}
		
	}

	renderPickerModal = () => {
		const {activeModal} = this.state;
		return (<Modal
		animationType="fade"
		transparent={true}
		visible={!!activeModal}
		onRequestClose={() => this.togglePickerModal(null)}
		>
		<View style={styles.pickerModal}>
			<TouchableWithoutFeedback onPress={() => this.togglePickerModal(null)}>
			<View style={styles.pickerModalBackdrop} />
			</TouchableWithoutFeedback>

			{this.renderPicker(activeModal)}
		</View>
		</Modal>);
	}

	getProductMetafields = () => {
		const product = this.props.products.activeProduct;
		const { assignPrint } = this.props.products;
		console.log('getProductMetafields products data-->', JSON.stringify(product));
		filteringOptions = {};
		filtering = {};
		const metafields = {};
		
		if(!!product && product.variants) {
			product.variants.forEach(variant => {
				if(!!variant && variant.selectedOptions) {
					variant.selectedOptions.forEach(option => {
						let name = option.name;
						let value = option.value;
						if(!metafields[name]) {
							filtering[name] = null
							metafields[name] = [value];
						}else if(metafields[name].indexOf(value) < 0){
							metafields[name].push(value);
						}
					})
				}
			});
		}

		// if(!!product && product.tags){
		//   product.tags.forEach(tag => {
		//     const splittedTag = tag.split('=');

		//     if(splittedTag.length === 2){
		//       const tagKey = splittedTag[0];
		//       const tagValue = splittedTag[1];

		//       if(!metafields[tagKey]){
		//         metafields[tagKey] = [tagValue];
		//       }else if(metafields[tagKey].indexOf(tagValue) < 0){
		//         metafields[tagKey].push(tagValue);
		//       }
		//     }
		//   })
		// }
		console.log('metafields-->', JSON.stringify(metafields));

		for(let field in metafields){
			filteringOptions[field] = {
				label: capitalizeString(field.replace('_', ' ')),
				options: [`Select ${capitalizeString(field.replace('_', ' '))}`, ...metafields[field]],
			}
		}
		console.log('assignPrint-->', JSON.stringify(assignPrint));
		if(assignPrint != undefined){
			filteringOptions['finger_print'] = {
				label: "Print",
				// options: ['Take a Print', 'Choose a Print', 'Request a Print'],
				options: [assignPrint.fingerprint_title,'Take a Print', 'Choose a Print'],
			}

			this.props.selectProductAttributes("Fingerprint Title", assignPrint.fingerprint_title);
			this.props.selectProductAttributes("_Fingerprint File", assignPrint.fingerprint_file);

			this.setState({
				filtering : {
					...this.state.filtering,
					finger_print : assignPrint.fingerprint_title
				}
			})
		} else {
			filteringOptions['finger_print'] = {
				label: "Print",
				// options: ['Take a Print', 'Choose a Print', 'Request a Print'],
				options: ['Take a Print', 'Choose a Print'],
			}
		}
		
		
		// this.setState({
		// 	filtering : {
		// 		...filtering,
		// 		finger_print : "Take a Print"
		// 	}
		// })
	}

	renderFilteringDropdowns = () => {
		const {filtering} = this.state;
		const dropdowns = [];

		for(let option in filteringOptions){
			console.log('filtering[option]-->',filtering[option]);
			dropdowns.push(<Text key={`${option}-label`} style={[styles.sidemenuPickerTitle,{color: Colors.subheaderTextColor,}]}>{filteringOptions[option].label.toUpperCase()}</Text>);
			if(Platform.OS === 'ios'){
				dropdowns.push(
					<TouchableOpacity disabled={option == "finger_print"} style={[styles.dropdownMenu,{borderColor: Colors.yellowBackgroundColor,backgroundColor: Colors.secondaryBackgroundColor,}]} key={`dropdown-option-${option}`} onPress={() => this.togglePickerModal(option)}>
						<Text style={[styles.selectedPickerOptionText, {color: !!filtering[option] ? Colors.darkColor : Colors.primaryTextColor}]}>
							{filtering[option] ? capitalizeString(filtering[option].replace('_and_', ' & ')) : `Select a ${filteringOptions[option].label}`}
						</Text>
						{option != "finger_print" && <Image style={styles.pickerIcon} source={require('../../assets/icons/chev-down.png')} />}
					</TouchableOpacity>
				);
			}else{
				dropdowns.push(this.renderPicker(option));
			}
		}
		return dropdowns;
	}

	handleFingerprintsModalLayout = ({nativeEvent}) => {
		const {height} = nativeEvent.layout;
		this.setState({fingerprintsModalHeight: height});
	}

	componentDidMount(){
		const {userFingerprints} = this.props.fingerprints;
		this.getProductMetafields();
		if(userFingerprints.length === 0){
			this.props.loadFingerPrints();
		}
		this.updatePriceData()
	}

	renderModal = () =>{
		const { isModalVisible } = this.state;
		return(
			<Modal
				animationType="fade"
				transparent={true}
				visible={isModalVisible}
				onRequestClose={() => this.setState({isModalVisible : false})}
			>
				<View style={{flex:1, backgroundColor: Colors.transparent, alignItems:'center', justifyContent:'center'}}>
					<View style={{
						backgroundColor: Colors.secondaryBackgroundColor,
						borderRadius: 12,
						width: deviceWidth - 50,
						justifyContent: 'center',
						alignItems:'center',
						flex: 0.27,
						paddingVertical: 20,
					}} onLayout={this.handleFingerprintsModalLayout}>
						<Text style={styles.fingerprintsModalTitle}>{"Item added to cart!"}</Text>

						
						<TouchableOpacity style={styles.primaryButton} onPress={this.proceedToCheckout}>
							<Text style={styles.buttonText}>{"Proceed to checkout"}</Text>
						</TouchableOpacity>

						<TouchableOpacity style={[styles.secondaryButton, {marginVertical: 20}]} onPress={() => this.setState({isModalVisible : false},() => this.props.navigation.navigate("Collections"))}>
							<Text style={[styles.buttonText, {color: Colors.primaryBackgroundColor}]}>{"Continue shopping"}</Text>
						</TouchableOpacity>
						
					</View>
				</View>
			</Modal>	
		)
	}

	proceedToCheckout = () =>{
		// if(!!activeFingerprintId){
			this.setState({
				isModalVisible : false
			}, () =>{
				this.props.navigation.navigate('Checkout');
			})
			
		// }else{
		// 	Alert.alert('A finger print is required', 'Please select a finger print to continue.');
		// }
	}

	componentWillUnmount(){
		filteringOptions = {}
	}

	onPressAddToCart = () =>{
		const { isAddToCard } = this.state;
		const { checkOutId } = this.props.orders;
		// if(!isAddToCard){
		// 	const { filtering } = this.state;
		// 	switch (filtering.finger_print.toLowerCase()) {
		// 		case 'take a print':
	
		// 			this.takePrint()
		// 			break;
		// 		case 'choose a print':
		// 			// this.toggleFingerprintsModal(true)
		// 			this.props.navigation.navigate('FingerPrintVault', {from: 'Product'})
		// 			break;
		// 		case 'request a print':
		// 			this.requestPrint()
		// 			break;	
		// 		default:
		// 			break;
		// 	}
		// }else{

		this.setState({loading: true});
		const activeProduct = this.props.products.activeProduct;
		const {email, firstName, lastName, defaultAddress} = this.props.user.customerDetails;

		const productAttributes = this.props.products.selectedProductAttributes;
		const customAttributes = [];
		console.log('productAttributes-->', JSON.stringify(productAttributes)); 
		console.log('activeProduct-->', JSON.stringify(activeProduct)); 
		// {
		//   "key": "Fingerprint Title",
		//   "value": "Lion"
		// },
		// {
		//   "key": "_Fingerprint File",
		//   "value": "149"
		// }
		let variantId = '';
		activeProduct.variants.map((item) =>{
			// let title = item.title.toLowerCase().replace(/\s/g,'');
			// let titleAttribute = productAttributes.Metal.toLowerCase().replace(/\s/g,'')+"/"+productAttributes.Length;
			// console.log('title-->',title);
			// console.log('titleAttribute-->',titleAttribute);
			// if(title == titleAttribute){
			// 	variantId = item.id
			// }
			let isMatchCount = 0
			item.selectedOptions.map((data) =>{
				if(productAttributes[data.name] == data.value){
					isMatchCount++;
				}
			})
			if(item.selectedOptions.length == isMatchCount){
				variantId = item.id
			}
		})
		
		for(let attr in productAttributes){
			customAttributes.push({key: attr, value: productAttributes[attr]});
		}
		
		const lineItemsToAdd = [
			{
				variantId: variantId, // FIX ME
				quantity: 1,
				customAttributes
			}
		];
		if(checkOutId != undefined && checkOutId != ""){
			client.checkout.addLineItems(checkOutId, lineItemsToAdd).then((checkout) => {
				// Do something with the updated checkout
				console.log(checkout.lineItems); // Array with one additional line item
				this.props.setCartCount(checkout.lineItems.length || 0);
				this.setState({loading: false, isModalVisible : true});
			});
			
		}else{
			client.checkout.create().then((checkout) => {
				// Do something with the checkout
				console.log('checkout-->',checkout.id);
				
				this.props.setCheckOutId(checkout.id);
				this.props.setCheckOutIdInServer(checkout.id);
				this.props.checkoutCustomerAssociate(checkout.id);
				
				client.checkout.addLineItems(checkout.id, lineItemsToAdd).then((checkout) => {
					// Do something with the updated checkout
					this.props.setWebURL(checkout.webUrl);
					this.props.setCartCount(checkout.lineItems.length || 0);
					this.setState({loading: false, isModalVisible : true});
				});
				
			});	
		}
			
		// }
	}

	render() {
		const {activeModal, showFingerprintsModal, fingerprintsModalHeight, isNextButtonDisable} = this.state;
		const {navigation, products, fingerprints} = this.props;
		const product = products.activeProduct;
		const {userFingerprints} = fingerprints;
		const { price, isNextButton, loading } = this.state;

		return !!product ? (
			<Container>
				<_Header {...this.props} title={product.title} />
				<TouchableOpacity 
							style={{position:'absolute', top: 40, right: 15, zIndex:1}}
							onPress={() => this.props.navigation.navigate("Collections")} 
						>
							<Icon type={'Entypo'} name={'cross'} style={{fontSize: 30}} />
					</TouchableOpacity>
				<Content>

					<View style={styles.singleProductImages}>
						<SliderBox inactiveDotColor={'#D3D3D3'} dotColor={'#808080'} disableOnPress={true} images={product.images} style={styles.singleProductImage} imageLoadingColor={'#D3D3D3'} resizeMode={'contain'} 
						paginationBoxStyle={{position: "absolute",
							bottom: -10,
							padding: 0,
							alignItems: "center",
							alignSelf: "center",
							justifyContent: "center",
							paddingVertical: 10}} />
					</View>

					<Text style={styles.singleProductTitle}>{product.title}</Text>
					<Text style={styles.singleProductPrice}>${price && Number(price).toFixed(2) || Number(product.priceRange.minVariantPrice.amount).toFixed(2)}</Text>
					{!!product.description && <Text style={styles.singleProductDescription} numberOfLines={3} ellipsizeMode="tail">{product.description}</Text>}

					<View style={styles.singleProductVariants}>
						{this.renderFilteringDropdowns()}
					</View>

					{/* <Text style={styles.sectionTitle}>Choose Print</Text>

					<View style={styles.buttonsRow}>
						<TouchableOpacity style={styles.secondaryButton} onPress={this.takePrint}>
							<Text style={styles.secondaryButtonText}>{!!fingerprints.activeFingerprintId ? 'Take Another Print' : 'Take New Print'}</Text>
						</TouchableOpacity>
						<TouchableOpacity style={styles.secondaryButton} onPress={() => this.toggleFingerprintsModal(true)}>
							<Text style={styles.secondaryButtonText}>Select Existing Fingerprint</Text>
						</TouchableOpacity>
						<TouchableOpacity style={styles.secondaryButton} onPress={this.requestPrint}>
							<Text style={styles.secondaryButtonText}>Request Print</Text>
						</TouchableOpacity>
					</View> */}
					
				</Content>
				<View>
					{/* <TouchableOpacity disabled={isNextButtonDisable} style={[styles.primaryButton,{marginTop: 10, backgroundColor: isNextButtonDisable ? Colors.primaryTextColor : Colors.primaryBackgroundColor }]} onPress={this.proceedToCheckout}> */}
					<TouchableOpacity disabled={isNextButtonDisable} style={[styles.primaryButton,{marginVertical: 10, backgroundColor: isNextButtonDisable ? Colors.primaryTextColor : Colors.primaryBackgroundColor, flexDirection:'row', alignItems:'center', justifyContent:'center' }]} onPress={this.onPressAddToCart}>
						{!!loading && <ActivityIndicator />}
						<Text style={[styles.primaryButtonText,{marginLeft:10}]}>{isNextButton ? "Next" : "Add to cart"}</Text>
					</TouchableOpacity>
					{/* <TouchableOpacity style={[styles.secondaryButton,{marginTop: 10, alignSelf:'center'}]} onPress={() => this.props.navigation.goBack()}>
						<Text style={styles.secondaryButtonText}>Cancel</Text>
					</TouchableOpacity> */}
				</View>

				{/* <View style={styles.stickyFooter}>
					<TouchableOpacity style={styles.favoriteButton} onPress={() => this.toggleProductFavorite(product.id)}>
						{this.isFovoriteProduct(product.id) ? <HeartSolidIcon fill={Colors.primaryBackgroundColor} /> : <HeartHollowIcon stroke={Colors.primaryBackgroundColor} />}
					</TouchableOpacity>

					<TouchableOpacity style={styles.primaryButton} onPress={this.proceedToCheckout}>
						<Text style={styles.primaryButtonText}>Next</Text>
					</TouchableOpacity>
				</View> */}

				<Modal
					animationType="fade"
					transparent={true}
					visible={!!showFingerprintsModal}
					onRequestClose={() => this.toggleFingerprintsModal(false)}
				>
					<TouchableWithoutFeedback onPress={() => this.toggleFingerprintsModal(false)}>
						<View style={styles.fingerprintsModalBackdrop} />
					</TouchableWithoutFeedback>

					<View style={[styles.fingerprintsModal, {top: (deviceHeight - fingerprintsModalHeight) / 2}]} onLayout={this.handleFingerprintsModalLayout}>
						<Text style={styles.fingerprintsModalTitle}>{userFingerprints.length ? 'Select a Fingerprint' : 'Your vault is empty!'}</Text>

						{userFingerprints.map(fingerprint => (<TouchableOpacity style={styles.vaultItem} key={`fingerprints-list-${fingerprint.id}`} onPress={() => this.selectFingerprint(fingerprint.id)}>
							<Text style={styles.vaultItemName}>{fingerprint.fingerprint_title}</Text>
						</TouchableOpacity>))}
					</View>
				</Modal>	

			{Platform.OS === 'ios' && !!activeModal && this.renderPickerModal()}
			{this.renderModal()}
			</Container>
		) : <ActivityIndicator />
	}
}

const mapDispatchToProps = dispatch => ({
	loadFingerPrints: () => dispatch(loadFingerPrints()),
	setActiveFingerprintId: fingerprintId => dispatch(setActiveFingerprintId(fingerprintId)),
	selectProductAttributes: (property, value) => dispatch(selectProductAttributes(property, value)),
	addToFavoritedProducts: (customerId, productId) => dispatch(addToFavoritedProducts(customerId, productId)),
	removeFromFavoritedProducts: (customerId, productId) => dispatch(removeFromFavoritedProducts(customerId, productId)),
	setCheckOutId: (checkOutId) => dispatch(setCheckOutId(checkOutId)),
	setCartCount: (cartCount) => dispatch(setCartCount(cartCount)),
	setCheckOutIdInServer: (checkout_id) => dispatch(setCheckOutIdInServer(checkout_id)),
	checkoutCustomerAssociate: (checkout_id) => dispatch(checkoutCustomerAssociate(checkout_id)),
	setWebURL: (webUrl) => dispatch({
        type: 'SET_CHECKOUT_WEB_URL',
        payload: webUrl
    }),
});

const mapStateToProps = state => ({
	user: state.user,
	products: state.products,
	orders: state.orders,
	fingerprints: state.fingerprints,
});

export default connect(mapStateToProps, mapDispatchToProps)(ConfirmationProduct);