import axios from 'axios';
import AsyncStorage from '@react-native-community/async-storage';

import {graphqlApiUrl, storefrontAccessToken, apiUrl} from '../constants';
import { Alert } from 'react-native';
import _ from 'lodash';

export const loadCustomerDetails = () => {
	return async dispatch => {
    const customerAccessToken = await AsyncStorage.getItem('accessToken');

    axios({
      url: graphqlApiUrl,
      method: 'post',
      headers: {
        'X-Shopify-Storefront-Access-Token': storefrontAccessToken
      },
      data: {
        query: `
          query {
            customer(customerAccessToken: "${customerAccessToken}") {
              id
              email
              firstName
              lastName
              phone
              defaultAddress {
                address1
                city
                province
                zip
                country
              }        
            }
          }
        `
      }
    }).then(result => {
      const response = result.data;
      console.log('customer detail response -->', JSON.stringify(result.data));
      const customerDetails = response?.data?.customer;

      dispatch({
        type: 'LOADED_CUSTOMER_DETAILS',
        payload: customerDetails
      });
    });
  };
}

export const updateCustomerDetails = (customer, callback) => {
	return async dispatch => {
    const customerAccessToken = await AsyncStorage.getItem('accessToken');
    console.log('customer-->', JSON.stringify(customer));
    
    dispatch({
      type: 'UPDATING_CUSTOMER_DETAILS'
    });
    
    axios({
      url: graphqlApiUrl,
      method: 'post',
      headers: {
        'X-Shopify-Storefront-Access-Token': storefrontAccessToken
      },
      data: {
        query: `
          mutation customerUpdate($customerAccessToken: String!, $customer: CustomerUpdateInput!) {
            customerUpdate(customerAccessToken: $customerAccessToken, customer: $customer) {
              customer {
                id
                email
                firstName
                lastName
                phone
              }
              customerUserErrors {
                code
                field
                message
              }
            }
          }
        `,
        variables: {
          customerAccessToken,
          customer
        }
      }
    }).then(result => {
      const response = result.data;
      const customerDetails = response?.data?.customerUpdate?.customer;
      console.log('UPDATED_CUSTOMER_DETAILS response-->', JSON.stringify(response));
      if(customerDetails){
        Alert.alert("Success","Update Successfully")
        dispatch({
          type: 'UPDATED_CUSTOMER_DETAILS',
          payload: customerDetails
        });
        callback();
      }else{
        Alert.alert("Error",_.get(response,'data.customerUpdate.customerUserErrors[0].message'))
        dispatch({
          type: 'UPDATING_CUSTOMER_DETAILS_ERROR'
        });
      }
    });
  };
}

export const registerNotificationsToken = deviceToken => ({
  type: 'STORE_NOTIFICATIONS_TOKEN',
  payload: deviceToken
});

export const updateNotificationsToken = (deviceToken, devicePlatform) => {
	return async dispatch => {
    const customerAccessToken = await AsyncStorage.getItem('accessToken');

		axios.post(`${apiUrl}/devices/add/`, {
      registration_id: deviceToken,
      type: devicePlatform
    },
    {
      headers: {
        'STOREFRONT-CUSTOMER-ACCESS-TOKEN': customerAccessToken
      }
    })
    .then(res => {
      if (res.status === 201) {
        dispatch({
          type: 'UPDATED_NOTIFICATIONS_TOKEN',
          payload: null,
        });
      }
    })
    .catch(err => console.log('ERROR Updating the notifications token', err));
	};
}


