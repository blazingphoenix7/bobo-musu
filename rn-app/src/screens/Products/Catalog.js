import React, {Component} from 'react';
import {SafeAreaView, ScrollView, Text, View, Image, 
  TouchableOpacity, TouchableWithoutFeedback, Modal, Platform, FlatList, RefreshControl,
  ActivityIndicator, StyleSheet, Dimensions} from 'react-native'
import {Picker} from '@react-native-community/picker';
import MultiSlider from '@ptomasroos/react-native-multi-slider';
import {connect} from 'react-redux';
import _Header from '../../components/_Header';
import {capitalizeString} from '../../helpers';
import styles from './styles';
import {BackArrowIcon, HeartSolidIcon, HeartHollowIcon, XIcon} from '../../components/icons';
import * as Colors from '../../styles/colors';
import {loadProducts, setActiveProduct, addToFavoritedProducts, removeFromFavoritedProducts} from '../../actions/products';

const {width: deviceWidth, height: deviceHeight} = Dimensions.get('window');

let filteringOptions = {};
let min = null;
let max = null;

class Catalog extends Component{

	constructor(props){
		super(props);

		this.state = {
			showSidemenu: false,
			priceRange: [min, max],
			filtering: {},
			activeModal: null,
			productType: '',
			isRefresh : false
		}
	}
  
	togglePickerModal = modal => this.setState({activeModal: modal});

	onPriceRangeChange = values => this.setState({priceRange: values});

	toggleSidemenu = () => {
		const {showSidemenu} = this.state;
		this.setState({showSidemenu: !showSidemenu});
	}

	handlePickerChange = (itemValue, filterByKey) => {
		console.log('itemValue-->',JSON.stringify(itemValue));
		this.setState(state => {
			state.filtering[filterByKey] = JSON.parse(itemValue);
			state.activeModal = null;

			return state;
		}, () => {
			
			console.log('filtering-->', JSON.stringify(this.state.filtering));

			let query = '';
			Object.values(this.state.filtering).map((item,index) =>{
				if(item.value != '-'){
					query += `${item.value}`
					if(Object.values(this.state.filtering).length -1 != index ){
						query += ` AND `
					}
				}
			});
			
			console.log('query-->',query);

			if(query != ''){
				this.props.loadProducts({product_type: this.state.productType, tag: query});
			}else{
				this.props.loadProducts({product_type: this.state.productType});
			}
			
		});
  	}

	renderSliderLabels = ({oneMarkerValue, twoMarkerValue}) => (
		<View style={{flexDirection: 'row', justifyContent: 'space-between'}}>
			<Text style={{color: '#fff'}}>{"MIN: "+ new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD'}).format(oneMarkerValue)}</Text>
			<Text style={{color: '#fff'}}>{"MAX: "+ new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD'}).format(twoMarkerValue)}</Text>
		</View>
	);

	toggleProductFavorite = product => {
		const customerId = this.props.user.customerDetails.id;
		let {favoritedProducts} = this.props.products;
		if(this.isFovoriteProduct(product.id)){
			let selectedIndex = favoritedProducts.findIndex(x => x.graphql_product_id === product.id);
			favoritedProducts.splice(1,selectedIndex);
			this.props.setFavoriteProductData(favoritedProducts);
			this.props.removeFromFavoritedProducts(customerId, product.id);
		}else{
			
			let data = {
				// "id": 146,
				// "product_id": 4618256089151,
				"graphql_product_id": product.id,
				"customer_id": customerId,
				"graphql_customer_id": customerId,
				...product
			}
			favoritedProducts.unshift(data);
			this.props.setFavoriteProductData([...favoritedProducts]);

			this.props.addToFavoritedProducts(customerId, product.id);
		}
	}

	renderPicker = activeModal => {
		const selectedValue = this.state.filtering[activeModal];
		const options = filteringOptions[activeModal].options;
		console.log('selectedValue-->', JSON.stringify(selectedValue));
		
		if(Platform.OS === 'ios'){
			return (
				<Picker
					key={activeModal}
					style={Platform.OS === 'ios' ? styles.pickerItemsWrap : {color: '#fff', marginLeft:10 }}
					dropdownIconColor='#ffffff'
					mode="dialog"
					selectedValue={selectedValue && JSON.stringify(selectedValue) || 'Select'}
					onValueChange={(itemValue, itemIndex) => this.handlePickerChange(itemValue, activeModal)}
				>
					{options.map(option => <Picker.Item key={`picker-${option.title}`} label={capitalizeString(option.title.replace('_and_', ' & '))} value={JSON.stringify(option)} />)}
				</Picker>
			);
		}else{
			return (
				<View style={{borderWidth:1, marginTop:10, borderColor:'#fff'}}>
					<Picker
						key={activeModal}
						style={Platform.OS === 'ios' ? styles.pickerItemsWrap : {color: '#fff', marginLeft:10 }}
						dropdownIconColor='#ffffff'
						mode="dialog"
						selectedValue={selectedValue && JSON.stringify(selectedValue) || 'Select'}
						onValueChange={(itemValue, itemIndex) => this.handlePickerChange(itemValue, activeModal)}
					>
						{options.map(option => <Picker.Item key={`picker-${option.title}`} label={option.title.toUpperCase().replace('_and_', ' & ')} value={JSON.stringify(option)} />)}
					</Picker>
				</View>
			);
		}
		
	}

	openProduct = product => {
		this.props.setActiveProduct(product);
		this.props.navigation.navigate('Product');
	}

	renderPickerModal = () => {
		const {activeModal} = this.state;

		return (
			<Modal
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
			</Modal>
			);
	}

	getProductsMetafields = () => {

		const { productFilterData } = this.props.products
		
		filteringOptions = {};
		// const metafields = {};

		productFilterData.forEach(item => {
			let tagData = item.tags.map(x =>{
				return {
					title : x.split("=")[1] || x,
					value : x
				}
			})
			filteringOptions[item.title] = {
				// label: capitalizeString(item.title.replace('_', ' ')),
				label: item.title.toUpperCase().replace('_', ' '),
				options: [{title: `All`, value: '-'}, ...tagData],
			}
		})
		console.log('filteringOptions-->', JSON.stringify(filteringOptions));
	}

	renderFilteringDropdowns = () => {
		const {filtering} = this.state;
		const dropdowns = [];

		for(let option in filteringOptions){
			dropdowns.push(<Text key={`${option}-label`} style={[styles.sidemenuPickerTitle,]}>{filteringOptions[option].label}</Text>);

			if(Platform.OS === 'ios'){
				dropdowns.push(
					<TouchableOpacity style={styles.dropdownMenu} key={`${option}-dropdown-menu`} onPress={() => this.togglePickerModal(option)}>
						<Text style={[styles.selectedPickerOptionText]}>{filtering[option] ? capitalizeString(filtering[option].title.replace('_and_', ' & ')) : "All"}</Text>
						<Image style={[styles.pickerIcon,{tintColor: Colors.secondaryTextColor}]} source={require('../../assets/icons/chev-down.png')} />
					</TouchableOpacity>
				);
			}else{
				dropdowns.push(this.renderPicker(option));
			}
		}

		return dropdowns;
	}

	renderProducts = () => {
		const {products} = this.props.products;
		const {priceRange, filtering} = this.state;
		const minValue = priceRange[0] !== null ? priceRange[0] : min;
		const maxValue = priceRange[1] !== null ? priceRange[1] : max;
		const renderedProducts = [];

		products.forEach((product, index) => {
			const inRange = parseFloat(product.priceRange.minVariantPrice.amount) >= minValue && 
				parseFloat(product.priceRange.maxVariantPrice.amount) <= maxValue;

			let filtersApply = false;

			if(Object.keys(filtering).length){
				if(product.tags){
					product.tags.forEach(tag => {
						const splittedTag = tag.split('=');

						if(splittedTag.length === 2){
						const tagKey = splittedTag[0];
						const tagValue = splittedTag[1];

						if(!!filtering[tagKey] && filtering[tagKey] == tagValue){
							filtersApply = true;
						}
						}
					});
				}
			}else{
				filtersApply = true;
			}

			if(filtersApply && inRange || (minValue === null && maxValue === null)){
				renderedProducts.push(
					<View key={`product-${index}-${product.id}`} style={styles.productWrap}>
						<TouchableOpacity style={styles.product} onPress={() => this.openProduct(product)}>
							<Image source={{uri: product.images[0]}} style={styles.productImage} resizeMode="cover" />
							<Text style={styles.productPrice}>${product.priceRange.minVariantPrice.amount}</Text>

							<TouchableOpacity style={styles.productFavorite} onPress={() => this.toggleProductFavorite(product)}>
								{this.isFovoriteProduct(product.id) ? <HeartSolidIcon /> : <HeartHollowIcon />}
							</TouchableOpacity>
						</TouchableOpacity>
					</View>
				);
			}
		});

		return renderedProducts;
	}

	isFovoriteProduct = productId => {
		const {favoritedProducts} = this.props.products;
		let isFav = favoritedProducts.find(x => x.graphql_product_id === productId) != undefined;
		// for(let product of favoritedProducts){
		// 	if(product.graphql_product_id === productId){
		// 		return true;
		// 	}
		// }
		return isFav;
	}

	componentDidMount(){
		const productType = this.props.navigation.getParam('productType', null);
		this.getProductsMetafields();
		if(productType){
			this.setState({productType});
			this.props.loadProducts({product_type: productType});
		}
	}

	onRefresh = () => {
		this.setState({isRefresh : true})
		const productType = this.props.navigation.getParam('productType', null);
		if(productType){
			this.setState({productType});
			this.props.loadProducts({product_type: productType});
		}
	}

	renderItem = ({item}) => {
		return(
			<View style={styles.productWrap}>
				<TouchableOpacity style={styles.product} onPress={() => this.openProduct(item)}>
					<Image source={{uri: item.images[0]}} style={styles.productImage} resizeMode="contain" />
					
					<Text style={styles.productPrice}>${Number(item.priceRange.minVariantPrice.amount).toFixed(2)}</Text>

					<TouchableOpacity style={styles.productFavorite} onPress={() => this.toggleProductFavorite(item)}>
						{this.isFovoriteProduct(item.id) ? <HeartSolidIcon /> : <HeartHollowIcon />}
					</TouchableOpacity>
				</TouchableOpacity>
			</View>
		)
	}

	ListFooterComponent = () =>{
		const { isRefresh } = this.state;
		const { productLoading } = this.props.products;
		return(
			<View style={{alignItems:'center', justifyContent:'center'}}>
				{(productLoading && !isRefresh) && <ActivityIndicator />}
			</View>
		)
	}

	ListEmptyComponent = () => { 
		const  { productLoading } = this.props.products;
		return (
			<View style={{ alignItems:'center', justifyContent:'center' }}>
				{!productLoading && <Text style={styles.noRecordFound}>{"No record found"}</Text>}
			</View>
		)
	}

  	render(){
		const { showSidemenu, activeModal, priceRange, refreshing } = this.state;
		const  { productLoading } = this.props.products;
    	// if(showSidemenu){
		// 	this.getProductsMetafields()
    	// }

    	return (
			<SafeAreaView style={styles.container}>
				<_Header {...this.props} isCart />
				{/* <ScrollView style={styles.container} contentContainerStyle={styles.innerContainer}> */}
				<View style={{flex:1}}>
					<View style={styles.subheader}>
						<Text style={styles.subheaderTitle}>Catalog</Text>
						<TouchableOpacity onPress={this.toggleSidemenu}>
							<Image source={require('../../assets/icons/sorting.png')} />
						</TouchableOpacity>
					</View>
					<View style={{ flex:1 }}>
						<FlatList 
							data={this.props.products.products}
							numColumns={2}
							renderItem={this.renderItem}
							keyExtractor={(item,index) => index.toString()}
							ListFooterComponent={this.ListFooterComponent}
							ListEmptyComponent={this.ListEmptyComponent}
							style={{marginHorizontal : 10, flex:1}}
							// contentContainerStyle={{alignItems:'center'}}
							extraData={this.props}
							refreshControl={<RefreshControl refreshing={productLoading} onRefresh={this.onRefresh} />}
						/>
					</View>
				</View>

				{/* <View style={styles.productsWrap}>
					{this.renderProducts()}
				</View> */}
				{/* </ScrollView> */}

				{showSidemenu && (<View style={styles.sidemenuWrap}>
				
				{this.renderFilteringDropdowns()}

				<TouchableOpacity style={{position: 'absolute', top: 50, right: 25}} onPress={this.toggleSidemenu}>
					<XIcon fill="#FFF" />
				</TouchableOpacity>
				</View>)}

				{Platform.OS === 'ios' && !!activeModal && this.renderPickerModal()}
			</SafeAreaView>
    	)
  	}
}

const mapDispatchToProps = dispatch => ({
	loadProducts: (filters) => dispatch(loadProducts(filters)),
	setActiveProduct: product => dispatch(setActiveProduct(product)),
	addToFavoritedProducts: (customerId, productId) => dispatch(addToFavoritedProducts(customerId, productId)),
	removeFromFavoritedProducts: (customerId, productId) => dispatch(removeFromFavoritedProducts(customerId, productId)),
	setFavoriteProductData: (props) => dispatch({
		type: 'LOADED_FAVORITED_PRODUCTS',
		payload: props
	})
});

const mapStateToProps = state => ({
  products: state.products,
  user: state.user,
});

export default connect(mapStateToProps, mapDispatchToProps)(Catalog);