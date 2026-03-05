import React, { Component } from 'react';
import { SafeAreaView, RefreshControl, Text, View, Image, TouchableOpacity, Dimensions, Platform, FlatList } from 'react-native'
import Carousel, { ParallaxImage } from 'react-native-snap-carousel';
import { connect } from 'react-redux';
import AsyncStorage from '@react-native-community/async-storage';

import styles from './styles';
import { MenuIcon } from '../../components/icons';
import _Header from '../../components/_Header';
import { loadCollections, loadFavoritedProducts, loadFilterData } from '../../actions/products';
import { loadSidebarMenuRoutes, loadHomeSliders } from '../../actions/general';
import { updateNotificationsToken } from '../../actions/user';
import {loadFingerPrints, setTakenFingerPrintPhoto} from '../../actions/fingerprints';
import { getCheckOutId } from '../../actions/orders';

const { width: deviceWidth } = Dimensions.get('window')

class Collections extends Component {
	
	constructor(props){
		super(props);
		this.state = {
			sentNotificationsToken: false,
			refreshing: false
		}
		const { tempFingerPrintData } = props.fingerprints;
		console.log('tempFingerPrintData-->',tempFingerPrintData);
		if(tempFingerPrintData != undefined){
			this.props.setTakenFingerPrintPhoto(tempFingerPrintData.fingerprintPhoto)
			this.props.navigation.navigate("SingleFingerPrint",{from :tempFingerPrintData.backToScreen, fingerprintName : tempFingerPrintData.fingerprintName,hasFingerprintPhoto: true})
		}
	}

	openCollection = (productType) => {
		this.props.setProductDetail();
		this.props.navigation.navigate('Catalog', { productType });
	}

	takePrint = async () => {
		const skipTutorial = await AsyncStorage.getItem('skipTutorial');
		
		if(!!skipTutorial){
			this.props.navigation.navigate('TakeFingerPrint', {backToScreen: 'Collections'});
		}else{
			this.props.navigation.navigate('Tutorial', {backToScreen: 'Collections'});
		}
	}

	_renderItem = ({ item, index }, parallaxProps) => (
		<View style={styles.homeSlider}>
			<ParallaxImage
				source={{ uri: item.image }}
				containerStyle={styles.homeSliderImageContainer}
				style={styles.homeSliderImage}
				parallaxFactor={0.4}
				{...parallaxProps}
			/>
		</View>
	);

	componentDidUpdate(){
		const {customerDetails} = this.props.user;
		const {deviceToken} = this.props.general;

		if(!this.state.sentNotificationsToken && !!deviceToken && !!customerDetails && customerDetails.id){
			this.setState({sentNotificationsToken: true});
			this.props.updateNotificationsToken(deviceToken, Platform.OS);
		}
	}

	componentDidMount() {
		this.props.loadCollections();
		this.props.loadSidebarMenuRoutes();
		this.props.loadHomeSliders();
		this.props.loadFilterData();
		this.props.getCheckOutId();

		
		const {customerDetails} = this.props.user;
		if (!!customerDetails && customerDetails.id) {
			this.props.loadFavoritedProducts(customerDetails.id);
			this.props.loadFingerPrints();
		}
	}

	renderItem = ({ item }) => {
		return(
			<View key={item.id} style={styles.productWrap}>
				<TouchableOpacity style={styles.product} onPress={() => this.openCollection(item.title)}>
					{item.image && item.image.originalSrc ? (<Image source={{ uri: item.image.originalSrc }} style={styles.productImage} resizeMode="cover" />) : <Image source={require('../../assets/images/placeholder.jpg')} style={styles.productImage} resizeMode="cover" />}
					
					<Text style={[styles.productPrice,{marginBottom: 0}]}>{item.title}</Text>
					<Text style={styles.productCount}>{`${item.productsCount} items`}</Text>
				</TouchableOpacity>
			</View>
		)
	}

	ListHeaderComponent = () => {
		const { homeSlides } = this.props.general;
		return(
			<View style={styles.homeSliderWrapper}>
				<Carousel
					sliderWidth={deviceWidth}
					sliderHeight={260}
					itemWidth={deviceWidth}
					data={homeSlides}
					renderItem={this._renderItem}
					hasParallaxImages={true}
				/>
			</View>
		)
	}

	onRefresh = () =>{
		this.setState({
			refreshing: true
		},() =>{
			this.props.loadCollections(() => {
				this.setState({
					refreshing: false
				})
			});
		});
	}

  	render() {
		const { collections } = this.props.products;
		const { refreshing } = this.state;
    	return (
			<SafeAreaView style={styles.container}>
				<_Header {...this.props} isMenu isCart />
				<FlatList 
					data={collections}
					numColumns={2}
					renderItem={this.renderItem}
					ListHeaderComponent={this.ListHeaderComponent}
					keyExtractor={(item,index) => index.toString()}
					showsVerticalScrollIndicator={false}
					contentContainerStyle={{alignItems:'center'}}
					refreshControl={<RefreshControl refreshing={refreshing} onRefresh={this.onRefresh} />}
				/>
				<View style={[styles.stickyFooter, {justifyContent: 'center', alignItems: 'center', backgroundColor: 'none'}]}>
					<TouchableOpacity style={styles.primaryButton} onPress={this.takePrint}>
						<Text style={styles.primaryButtonText}>Take a Print</Text>
					</TouchableOpacity>
				</View>
			</SafeAreaView>
    	)
  	}
}

const mapDispatchToProps = dispatch => ({
  loadCollections: (callback) => dispatch(loadCollections(callback)),
  loadFavoritedProducts: customerId => dispatch(loadFavoritedProducts(customerId)),
  loadSidebarMenuRoutes: () => dispatch(loadSidebarMenuRoutes()),
  loadFilterData: () => dispatch(loadFilterData()),
  loadHomeSliders: () => dispatch(loadHomeSliders()),
  updateNotificationsToken: (deviceToken, devicePlatform) => dispatch(updateNotificationsToken(deviceToken, devicePlatform)),
  loadFingerPrints: () => dispatch(loadFingerPrints()),
  setTakenFingerPrintPhoto: fingerprintPhoto => dispatch(setTakenFingerPrintPhoto(fingerprintPhoto)),
  getCheckOutId: () => dispatch(getCheckOutId()),
  setProductDetail : () => dispatch({
    type: 'LOADED_PRODUCTS',
    payload: []
  })
});

const mapStateToProps = state => ({
  user: state.user,
  general: state.general,
  products: state.products,
  fingerprints: state.fingerprints,
});

export default connect(mapStateToProps, mapDispatchToProps)(Collections);