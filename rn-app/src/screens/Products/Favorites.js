import React, {Component} from 'react';
import { SafeAreaView, ScrollView, View, Text, TouchableOpacity, Image, Alert } from 'react-native';
import {connect} from 'react-redux';
import { Container, Content } from 'native-base';
import styles from './styles';
import {MenuIcon, HeartSolidIcon, HeartHollowIcon} from "../../components/icons";
import {loadFavoritedProducts, setActiveProduct, addToFavoritedProducts, removeFromFavoritedProducts} from '../../actions/products';
import {capitalizeString} from '../../helpers';
import _Header from '../../components/_Header';
class Favorites extends Component {

  componentDidMount(){
    // const customerId = this.props.user.customerDetails.id;
    // this.props.loadFavoritedProducts(customerId);
    
  }

  openProduct = product => {
		this.props.setActiveProduct(product);
		this.props.navigation.navigate('Product');
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
  
  toggleProductFavorite = product => {
    Alert.alert("Bobo musu", "Are you sure want to remove it from favorites?",[
      {
        text: "No", onPress:() =>{  console.log("Cancel")}, style : 'cancel'
      },
      {
        text: "Yes", onPress:() =>{
          const customerId = this.props.user.customerDetails.id;
          this.props.removeFromFavoritedProducts(customerId, product.id);
        },
      },
    ])
		// const customerId = this.props.user.customerDetails.id;
    // let {favoritedProducts} = this.props.products;
    // console.log('before favoritedProducts-->', JSON.stringify(favoritedProducts));
		// // if(this.isFovoriteProduct(product.id)){
    //   let selectedIndex = favoritedProducts.findIndex(x => x.graphql_product_id === product.id);
    //   console.log('selectedIndex-->', selectedIndex)
    //   favoritedProducts.splice(1,selectedIndex);
    //   console.log('after favoritedProducts-->', JSON.stringify(favoritedProducts));
		// 	this.props.setFavoriteProductData([favoritedProducts]);
			// this.props.removeFromFavoritedProducts(customerId, product.id);
		// }else{
			
		// 	let data = {
		// 		// "id": 146,
		// 		// "product_id": 4618256089151,
		// 		"graphql_product_id": product.id,
		// 		"customer_id": customerId,
    //     "graphql_customer_id": customerId,
    //     ...product
		// 	}
		// 	favoritedProducts.push(data);
		// 	this.props.setFavoriteProductData(favoritedProducts);

		// 	this.props.addToFavoritedProducts(customerId, product.id);
		// }
	}

  render() {
    const {favoritedProducts} = this.props.products;
    console.log('favoritedProducts-->', JSON.stringify(favoritedProducts));
    return (<SafeAreaView style={styles.container}>
      <_Header {...this.props} title={'Favorites'} isMenu />
      <ScrollView style={styles.container} contentContainerStyle={styles.innerContainer}>
        {/* <View style={[styles.header, {borderBottomWidth: 0}]}>
          <TouchableOpacity onPress={() => this.props.navigation.openDrawer()}>
            <MenuIcon />
          </TouchableOpacity>
          <Text style={styles.singleProductCategory}>Favorites</Text>
        </View> */}

        <View style={styles.productsWrap}>

          {favoritedProducts.length > 0  ? favoritedProducts.map((item, index)=> (
              <View key={index} style={styles.productWrap}>
              <TouchableOpacity style={[styles.product, styles.favoriteProduct]} onPress={() => this.openProduct(item)}>
                {item.images && item.images[0] ? (<Image source={{ uri: item.images[0] }} style={styles.favoriteProductImage} resizeMode="contain" />) : <Image source={require('../../assets/images/placeholder.jpg')} style={styles.productImage} resizeMode="cover" />}
                
                <Text style={styles.productPrice}>${Number(item?.priceRange?.minVariantPrice?.amount || 0).toFixed(2)}</Text>
                <TouchableOpacity style={styles.productFavorite} onPress={() => this.toggleProductFavorite(item)}>
                  {this.isFovoriteProduct(item.id) ? <HeartSolidIcon /> : <HeartHollowIcon />}
                </TouchableOpacity>
              </TouchableOpacity>
            </View>
          )) : 
          <View style={styles.noRecordFoundView}>
            <Text style={styles.noRecordText}>{"No Record found"}</Text>  
          </View>}
        </View>
      </ScrollView>
    </SafeAreaView>)
  }
}

const mapDispatchToProps = dispatch => ({
  loadFavoritedProducts: customerId => dispatch(loadFavoritedProducts(customerId)),
  setActiveProduct: product => dispatch(setActiveProduct(product)),
  setFavoriteProductData: (props) => dispatch({
		type: 'LOADED_FAVORITED_PRODUCTS',
		payload: props
  }),
  addToFavoritedProducts: (customerId, productId) => dispatch(addToFavoritedProducts(customerId, productId)),
  removeFromFavoritedProducts: (customerId, productId) => dispatch(removeFromFavoritedProducts(customerId, productId)),
});

const mapStateToProps = state => ({
  user: state.user,
  products: state.products,
});

export default connect(mapStateToProps, mapDispatchToProps)(Favorites);
