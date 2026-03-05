import React, {Component} from 'react';
import {SafeAreaView, Image, ScrollView, View, Text, TouchableOpacity, ActivityIndicator} from 'react-native';
import {WebView} from 'react-native-webview';
import {connect} from 'react-redux';
import AsyncStorage from '@react-native-community/async-storage';

import styles from './styles';
import {BackArrowIcon} from '../../components/icons';
import {orderCheckout,setCheckOutIdInServer, resetCheckoutWebUrl, setCartCount} from '../../actions/orders';
import client from '../../config/shophify';
import _Header from '../../components/_Header';
class Checkout extends Component {
  state = {
    headerHeight: 62,
    scrollViewHeight: 600,
    webUrl: null,
  }

  goBack = () => {
    this.props.navigation.navigate('Collections');
  }

  handleHeaderLayout = ({nativeEvent}) => {
    const {height} = nativeEvent.layout;
    this.setState({headerHeight: height});
  }

  handleScrollViewLayout = ({nativeEvent}) => {
    const {height} = nativeEvent.layout;
    this.setState({scrollViewHeight: height});
  }

  onWebViewUrlChange = navState => {
    if(navState.url.search('/thank_you') > 0){
      setTimeout(() =>{
        this.setState({
          // webUrl: null
        });

        this.props.resetCheckoutWebUrl();
        this.props.setCheckOutIdInServer('');
        this.props.setCartCount(0);
        // this.props.navigation.navigate('Collections');
      }, 5000);
    }
  }

  componentDidUpdate(){

    const {checkoutWebUrl} = this.props.orders;

    console.log('checkoutWebUrl-->',checkoutWebUrl);
    if(!!checkoutWebUrl && !this.state.webUrl){
      this.setState({webUrl: checkoutWebUrl});
    }
  }

  componentDidMount() {
  }

  render() {
    const {scrollViewHeight, headerHeight, webUrl} = this.state;
    const { customerAccessToken } = this.props.user;
    return (
      <SafeAreaView style={styles.container}>
        <_Header {...this.props} title={'Checkout'} onPress={this.goBack} />
        <ScrollView style={styles.container} contentContainerStyle={styles.innerContainer} onLayout={this.handleScrollViewLayout}>
          
          {!!webUrl ? 
            <WebView
              cacheEnabled={false}
              incognito
              style={[styles.webview, {height: scrollViewHeight - headerHeight}]}
              source={{
                uri: webUrl,
                headers: { "X-Shopify-Customer-Access-Token": customerAccessToken.accessToken }
              }}
              originWhitelist={['*']}
              onNavigationStateChange={this.onWebViewUrlChange}
              startInLoadingState={true}
              // renderLoading={() => <ActivityIndicator />}
          /> : (
            <ActivityIndicator />
          )}
        </ScrollView>
      </SafeAreaView>
    )
  }
}

const mapDispatchToProps = dispatch => ({
  orderCheckout: order => dispatch(orderCheckout(order)),
  resetCheckoutWebUrl: () => dispatch(resetCheckoutWebUrl()),
  setCheckOutIdInServer: (checkout_id) => dispatch(setCheckOutIdInServer(checkout_id)),
  setCartCount: (cart_count) => dispatch(setCartCount(cart_count)),
});

const mapStateToProps = state => ({
  products: state.products,
  orders: state.orders,
  user: state.user
});

export default connect(mapStateToProps, mapDispatchToProps)(Checkout);