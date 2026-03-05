import axios from 'axios';
import AsyncStorage from '@react-native-community/async-storage';
import {graphqlAdminApiUrl, adminAccessToken, graphqlApiUrl, storefrontAccessToken} from '../constants';
import {apiUrl} from '../constants';

export const loadCustomerOrders1 = customerId => {
	return async dispatch => {
    console.log('customerId-->',customerId);
    axios({
      url: graphqlAdminApiUrl,
      method: 'post',
      headers: {
        'X-Shopify-Access-Token': adminAccessToken
      },
      data: {
        query: `
          query {
            customer(id: "${customerId}") {
              orders(first: 8) {
                edges{
                  node{
                    id
                    name
                    displayFulfillmentStatus
                    subtotalPriceSet {
                      presentmentMoney {
                        amount
                      }
                    }
                    lineItems (first:10) {
                      edges {
                        node {
                          id
                          name
                          title
                          product{
                            description
                          }
                          customAttributes{
                            key
                            value
                          }
                          fulfillmentStatus
                          originalUnitPriceSet{
                            presentmentMoney{
                              amount
                            }
                          }
                          variant {
                            id
                            selectedOptions{
                              name
                              value
                            }
                          }
                          variantTitle
                          image {
                            transformedSrc
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        `
      }
    }).then(result => {
      console.log('loadCustomerOrders result-->', JSON.stringify(result.data))
      dispatch({
        type: 'LOADED_CUSTOMER_ORDERS',
        payload: result.data
      });
    });
  };
}

export const loadCustomerOrders = customerId => {
  return async (dispatch, getStore) => {
    const customerAccessToken = await AsyncStorage.getItem('accessToken');
    console.log('apuUrl-->',`${apiUrl}/customers/orders/`);
    console.log('customerAccessToken-->',customerAccessToken);
		axios.get(`${apiUrl}/customers/orders/`, {
		  headers: {
			  'STOREFRONT-CUSTOMER-ACCESS-TOKEN': customerAccessToken
			}
		})
		.then(res => {
      console.log('loadCustomerOrders-->', JSON.stringify(res));
      if (res.status === 200) {
        dispatch({
          type: 'LOADED_CUSTOMER_ORDERS',
          payload: res?.data?.orders || []
        });
      }
		})
		.catch(err => console.log('ERROR', err));
  }
}

export const orderCheckout = order => {
	return async dispatch => {
    axios({
      url: graphqlApiUrl,
      method: 'post',
      headers: {
        'X-Shopify-Storefront-Access-Token': storefrontAccessToken
      },
      data: {
        query: `
        mutation checkoutCreate($input: CheckoutCreateInput!) {
          checkoutCreate(input: $input) {
            checkout {
              id
              webUrl
            }
            checkoutUserErrors {
              code
              field
              message
            }
          }
        }
      `,
      variables: {
        input: order
      }
      }
    }).then(result => {
      console.log('checkoutCreate-->',JSON.stringify(result.data));
      const webUrl = result.data?.data?.checkoutCreate?.checkout?.webUrl

      dispatch({
        type: 'SET_CHECKOUT_WEB_URL',
        payload: webUrl
      });
    });
  };
}

export const getCartData = (checkOutId) => {
	return async (dispatch, getStore) => {

    if(checkOutId == undefined){
      checkOutId = getStore().orders.checkOutId;
    }
    
    if(checkOutId != undefined && checkOutId != ''){
      client.checkout.fetch(checkOutId).then((checkout) => {
        // Do something with the checkout
        console.log('getCartData-->',JSON.stringify(checkout));
        dispatch({
          type: 'SET_CHECKOUT_WEB_URL',
          payload: checkout.webUrl
        })
        dispatch(setCartCount(checkout.lineItems.length || 0));
        
        // this.setState({isModalVisible : true})
      });
    }else{
      dispatch(setCartCount(0));
    }
    
  };
}

export const getCheckOutId = () => {
	return async (dispatch, getStore) => {
    const customerAccessToken = await AsyncStorage.getItem('accessToken');
    console.log('apuUrl-->',`${apiUrl}/customer-checkout-id/`);
    console.log('customerAccessToken-->',customerAccessToken);
		axios.get(`${apiUrl}/customer-checkout-id/`, {
		  headers: {
			  'STOREFRONT-CUSTOMER-ACCESS-TOKEN': customerAccessToken
			}
		})
		.then(res => {
      console.log('getCheckOutId-->', JSON.stringify(res));
      if (res.status === 200) {
        dispatch(setCheckOutId(res.data.checkout_id));
        dispatch(getCartData(res.data.checkout_id));
        dispatch(checkoutCustomerAssociate(res.data.checkout_id));
      }
		})
		.catch(err => console.log('ERROR', err));
  }
}

export const setCheckOutIdInServer = (checkout_id) => {
	return async (dispatch, getStore) => {
    const customerAccessToken = await AsyncStorage.getItem('accessToken');

		axios.post(`${apiUrl}/customer-checkout-id/`, {
      checkout_id : checkout_id
			}, {
		headers: {
			'STOREFRONT-CUSTOMER-ACCESS-TOKEN': customerAccessToken
				}
			})
		.then(res => {
      console.log('setCheckOutIdInServer-->', JSON.stringify(res));
      if (res.status === 200) {
        dispatch(setCheckOutId(res.data.checkout_id));
      }
		})
		.catch(err => console.log('ERROR', err));
  }
}

export const checkoutCustomerAssociate = (checkoutId) => {
  return async (dispatch, getStore) => {
    let customerAccessToken = getStore().user.customerAccessToken.accessToken;
    
    axios({
      url: graphqlApiUrl,
      method: 'post',
      headers: {
        'X-Shopify-Storefront-Access-Token': storefrontAccessToken
      },
      data: {
        query: `
          mutation checkoutCustomerAssociateV2($checkoutId: ID!, $customerAccessToken: String!) {
            checkoutCustomerAssociateV2(checkoutId: $checkoutId, customerAccessToken: $customerAccessToken) {
              checkout {
                id
              }
              checkoutUserErrors {
                code
                field
                message
              }
              customer {
                id
              }
            }
          }
        `,
        variables: {
          "checkoutId": checkoutId.toString(),
          "customerAccessToken": customerAccessToken.toString()
        }
      }
    }).then(async result => {
      console.log("checkoutCustomerAssociate-->", JSON.stringify(result));
    }).catch((error) =>{
      console.log("checkoutCustomerAssociate error-->", JSON.stringify(error));
    })
  };
}

export const resetCheckoutWebUrl = () => ({
  type: 'SET_CHECKOUT_WEB_URL',
  payload: null
})

export const setCheckOutId = (checkOutId) => ({
  type: 'SET_CHECKOUT_ID',
  payload: checkOutId
})

export const setCartCount = (cartCount) => ({
  type: 'SET_CART_COUNT',
  payload: cartCount
})

export const getOrderFulfillmentData = (orderId, fulfillmentId, callback) => {
	return async dispatch => {
    // {{base_url}}/app/customers/orders/2863228158015/fulfillments/2697519595583/events/
    // {{base_url}}/app/customers/orders/2844972384319/fulfillments/2676998438975/
    console.log("URL-->",`${apiUrl}/customers/orders/${orderId}/fulfillments/${fulfillmentId}/events/`);
    const customerAccessToken = await AsyncStorage.getItem('accessToken');
    axios.get(`${apiUrl}/customers/orders/${orderId}/fulfillments/${fulfillmentId}/events/`, {
      headers: {
        'STOREFRONT-CUSTOMER-ACCESS-TOKEN': customerAccessToken
			}
		})
    .then(res => {
        console.log('getOrderFulfillmentData-->',JSON.stringify(res.data));
      if (res.status === 200) {
        dispatch({
          type : "SET_FULFILLMENT_DATA",
          payload: res.data && Array.isArray(res.data) && res.data.pop() || undefined
        })
        callback()
      }
    })
    .catch(err => {
      callback()
      console.log('ERROR', err)
    });

    // const customerAccessToken = await AsyncStorage.getItem('accessToken');
    // axios.get(`${apiUrl}/customers/orders/${orderId}/`, {
    //   headers: {
    //     'STOREFRONT-CUSTOMER-ACCESS-TOKEN': customerAccessToken
		// 	}
		// })
    // .then(res => {
    //     console.log('getOrderFulfillmentData-->',JSON.stringify(res.data));
    //   if (res.status === 200) {
		
    //   }
    // })
    // .catch(err => console.log('ERROR', err));
	
    // axios({
    //   url: graphqlApiUrl,
    //   method: 'post',
    //   headers: {
    //     'X-Shopify-Storefront-Access-Token': storefrontAccessToken
    //   },
    //   data: {
    //     query: `
    //       {
    //         order(id: "gid://shopify/Order/2830821490751") {
    //           fulfillments(first:10){
    //             id
    //             trackingInfo {
    //               company
    //               number
    //               url
    //             }
    //           }
    //         }
    //       }
    //     `,
    //   }
    // }).then(result => {
    //   console.log('getOrderFulfillmentData-->',JSON.stringify(result));
    //   // const webUrl = result.data?.data?.checkoutCreate?.checkout?.webUrl

    //   // dispatch({
    //   //   type: 'SET_CHECKOUT_WEB_URL',
    //   //   payload: webUrl
    //   // });
    // });
  };
}