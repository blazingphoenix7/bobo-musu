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
import {selectProductAttributes, addToFavoritedProducts, removeFromFavoritedProducts, setProductVariants} from '../../actions/products';
import {loadFingerPrints, setActiveFingerprintId} from '../../actions/fingerprints';
import {capitalizeString} from '../../helpers';
import { Container, Content, Card } from 'native-base';
import { filter } from 'lodash';
// import Modal from 'react-native-modal';

let filteringOptions = {};
const {height: deviceHeight, width: deviceWidth} = Dimensions.get('window');

class Product extends Component {

	constructor(props){
		super(props);
		this.state = {
			filtering: {},
			activeModal: null,
			showFingerprintsModal: false,
			fingerprintsModalHeight: 0,
			price : undefined,
			isNextButtonDisable : true,
			isModalVisible : false
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
		const {activeModal} = this.state;
		if(pickerKey != "finger_print"){
			this.props.selectProductAttributes(pickerKey, itemValue);
		}
		
		
		this.setState(state => {
			state.filtering[pickerKey] = itemValue !== 'Select '+pickerKey ? itemValue : null;
			state.activeModal = null;
			return state;
		},() => {
			console.log('filtering-->',JSON.stringify(this.state.filtering));
			this.props.setProductVariants(this.state.filtering);
			let isNextButtonDisable = false
			for(let filterValue in this.state.filtering){
				console.log('filterValue-->',this.state.filtering[filterValue]);
				if(this.state.filtering[filterValue] == null){
					isNextButtonDisable = true;
					break;
				}else{
					isNextButtonDisable = false;
				}
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
		});
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

	proceedToCheckout = () => {
		const { activeFingerprintId } = this.props.fingerprints;
		const { filtering } = this.state;

		console.log("filtering-->", filtering.finger_print.toLowerCase());
		switch (filtering.finger_print.toLowerCase()) {
			case 'take a print':

				this.takePrint()
				break;
			case 'choose a print':
				// this.toggleFingerprintsModal(true)
				this.props.navigation.navigate('FingerPrintVault', {from: 'Product'})
				break;
			case 'request a print':
				this.requestPrint()
				break;	
			default:
				break;
		}
		
		return;
		if(!!activeFingerprintId){
			this.props.navigation.navigate('Checkout');
		}else{
			Alert.alert('A finger print is required', 'Please select a finger print to continue.');
		}
	}

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
						style={Platform.OS === 'ios' ? styles.pickerItemsWrap : {}}
						mode="dialog"
						selectedValue={selectedValue || '-'}
						onValueChange={(itemValue, itemIndex) => this.handlePickerChange(itemValue, activeModal)}
					>
						{options.map(option => <Picker.Item key={option} label={capitalizeString(option.toUpperCase().replace('_and_', ' & '))} value={option} />)}
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
		const {customerDetails} = this.props.user;
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

		if(customerDetails != undefined){
			filteringOptions['finger_print'] = {
				label: "Print",
				options: ['Take a Print', 'Choose a Print'],
			}
		}else{
			filteringOptions['finger_print'] = {
				label: "Print",
				options: ['Take a Print'],
			}
		}
		
		
		this.setState({
			filtering : {
				...filtering,
				finger_print : "Take a Print"
			}
		})
	}

	renderFilteringDropdowns = () => {
		const {filtering} = this.state;
		const dropdowns = [];

		for(let option in filteringOptions){
			dropdowns.push(<Text key={`${option}-label`} style={[styles.sidemenuPickerTitle,{color: Colors.subheaderTextColor,}]}>{filteringOptions[option].label.toUpperCase()}</Text>);
			if(Platform.OS === 'ios'){
				dropdowns.push(
					<TouchableOpacity style={[styles.dropdownMenu,{borderColor: Colors.yellowBackgroundColor,backgroundColor: Colors.secondaryBackgroundColor,}]} key={`dropdown-option-${option}`} onPress={() => this.togglePickerModal(option)}>
						<Text style={[styles.selectedPickerOptionText, {color: !!filtering[option] ? Colors.darkColor : Colors.primaryTextColor}]}>
							{filtering[option] ? capitalizeString(filtering[option].replace('_and_', ' & ')) : `Select a ${filteringOptions[option].label}`}
						</Text>
						<Image style={styles.pickerIcon} source={require('../../assets/icons/chev-down.png')} />
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
	}

	renderModal = () =>{
		const { isModalVisible } = this.state;
		return(
			<Modal
					animationType="fade"
					transparent={true}
					visible={!!isModalVisible}
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

						
							<TouchableOpacity style={styles.primaryButton} onPress={this.usePrint}>
								<Text style={styles.buttonText}>{"Proceed to checkout"}</Text>
							</TouchableOpacity>

							<TouchableOpacity style={[styles.secondaryButton, {marginVertical: 20}]} onPress={() => this.setState({isModalVisible : false},() =>this.props.navigation.goBack())}>
								<Text style={[styles.buttonText, {color: Colors.primaryBackgroundColor}]}>{"Continue shopping"}</Text>
							</TouchableOpacity>
						
					</View>
				</View>
			</Modal>	
		)
	}

	componentWillUnmount(){
		filteringOptions = {}
	}

	render() {
		const {activeModal, showFingerprintsModal, fingerprintsModalHeight, isNextButtonDisable} = this.state;
		const {navigation, products, fingerprints} = this.props;
		const product = products.activeProduct;
		const {userFingerprints} = fingerprints;
		const { price } = this.state;

		return !!product ? (
			<Container>
				<_Header {...this.props} title={product.title} />
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
					<TouchableOpacity disabled={isNextButtonDisable} style={[styles.primaryButton,{marginTop: 10,marginBottom:20, backgroundColor: isNextButtonDisable ? Colors.primaryTextColor : Colors.primaryBackgroundColor }]} onPress={this.proceedToCheckout}>
					{/* <TouchableOpacity disabled={isNextButtonDisable} style={[styles.primaryButton,{marginTop: 10, backgroundColor: isNextButtonDisable ? Colors.primaryTextColor : Colors.primaryBackgroundColor }]} onPress={() => this.setState({isModalVisible : true})}> */}
						<Text style={styles.primaryButtonText}>Next</Text>
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
	setProductVariants: (variants) => dispatch(setProductVariants(variants)),
});

const mapStateToProps = state => ({
	user: state.user,
	products: state.products,
	fingerprints: state.fingerprints,
});

export default connect(mapStateToProps, mapDispatchToProps)(Product);