import React, {Component} from 'react';
import {SafeAreaView, ScrollView, View, Text, TouchableOpacity, Image} from 'react-native';
import {connect} from 'react-redux';

import styles from './styles';
import {MenuIcon, HeartSolidIcon, HeartHollowIcon} from "../../components/icons";
import {loadCustomerOrders} from '../../actions/orders';
import {capitalizeString} from '../../helpers';
import {addToFavoritedProducts, removeFromFavoritedProducts} from '../../actions/products';
import LinearGradient from 'react-native-linear-gradient';
import * as Colors from '../../styles/colors'
import { NavigationEvents } from 'react-navigation';
import _Header from '../../components/_Header';
class MyOrders extends Component {


  onPressItem = (productId) =>{
    this.props.navigation.navigate("ProductDetails",{productId});
  }

  getStatusBackgroundColor = (status) =>{
    if(status == null){
      return [Colors.primaryColor,Colors.blueBackgroundColor]
    }else if(status == 'fulfilled'){
      return [Colors.blueBackgroundColor,Colors.blueBackgroundColor]
    }else{
      return [Colors.primaryColor,Colors.blueBackgroundColor]
    }
  }

  getStatusText = (status) =>{
    if(status == null){
      return "In Progress";
    }else if(status == 'fulfilled'){
      return "Shipped";
    }else{
      return "In Progress"
    }
  }

  render() {
    const {orders} = this.props.orders;
    console.log('orders-->', JSON.stringify(orders));
    return (
    <SafeAreaView style={styles.container}>
      <NavigationEvents
        onWillFocus={payload => console.log('will focus', payload)}
        onDidFocus={payload => {
          const customerId = this.props.user.customerDetails.id;
          this.props.loadCustomerOrders(customerId);
        }}
        onWillBlur={payload => console.log('will blur', payload)}
        onDidBlur={payload => console.log('did blur', payload)}
        />
      {/* <View style={[styles.header, {borderBottomWidth: 0}]}>
          <TouchableOpacity onPress={() => this.props.navigation.openDrawer()}>
            <MenuIcon />
          </TouchableOpacity>
          <Text style={styles.singleProductCategory}>My Orders</Text>
        </View> */}
        <_Header {...this.props} title={'My Orders'} isMenu />
      <ScrollView style={styles.container} contentContainerStyle={styles.innerContainer}>
        

        <View style={styles.productsWrap}>
          {orders.length > 0 ? orders.map((product, index) => (<View key={product.id, index} style={styles.productWrap}>
            <TouchableOpacity style={styles.product} onPress={() => this.onPressItem(product)}>
              <Image source={{uri: product.image}} style={styles.myOrderProjectImage} resizeMode="contain" />
              <Text style={styles.productPrice}>${product.price}</Text>

              <LinearGradient start={{x: 0, y: 0}} end={{x: 1, y: 0}} colors={this.getStatusBackgroundColor(product.fulfillmentStatus)} style={styles.productFulfillmentStatusView}>
                <Text style={styles.productFulfillmentStatus}>{capitalizeString(this.getStatusText(product.fulfillmentStatus))}</Text>
              </LinearGradient>
              

            </TouchableOpacity>
          </View>))
          :
            <View style={styles.noRecordFoundView}>
              <Text style={styles.noRecordText}>{"No orders found"}</Text>  
            </View>
          }
        </View>
      </ScrollView>
    </SafeAreaView>)
  }
}

const mapDispatchToProps = dispatch => ({
  loadCustomerOrders: customerId => dispatch(loadCustomerOrders(customerId)),
  addToFavoritedProducts: (customerId, productId) => dispatch(addToFavoritedProducts(customerId, productId)),
	removeFromFavoritedProducts: (customerId, productId) => dispatch(removeFromFavoritedProducts(customerId, productId)),
	setFavoriteProductData: (props) => dispatch({
		type: 'LOADED_FAVORITED_PRODUCTS',
		payload: props
	})
});

const mapStateToProps = state => ({
  user: state.user,
  orders: state.orders,
  products: state.products,
});

export default connect(mapStateToProps, mapDispatchToProps)(MyOrders);
