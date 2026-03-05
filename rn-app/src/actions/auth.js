import axios from 'axios';
import AsyncStorage from '@react-native-community/async-storage';
import {Alert} from 'react-native';

import { graphqlApiUrl, storefrontAccessToken } from '../constants';
import {toastSuccess, toastError} from '../actions/general';
import { getCheckOutId } from '../actions/orders';

export const login = credentials => {
  return async dispatch => {
    axios({
      url: graphqlApiUrl,
      method: 'post',
      headers: {
        'X-Shopify-Storefront-Access-Token': storefrontAccessToken
      },
      data: {
        query: `
          mutation customerAccessTokenCreate($input: CustomerAccessTokenCreateInput!) {
            customerAccessTokenCreate(input: $input) {
              userErrors {
                field
                message
              }
              customerAccessToken {
                accessToken
                expiresAt
              }
            }
          }
        `,
        variables: {
          input: credentials
        }
      }
    }).then(async result => {
      const response = result.data;
      const customerAccessToken = response?.data?.customerAccessTokenCreate?.customerAccessToken;

      if(customerAccessToken){
        await AsyncStorage.setItem('accessToken', customerAccessToken.accessToken);
        await AsyncStorage.setItem('accessTokenExpiration', customerAccessToken.expiresAt);
        
        dispatch({
          type: 'STORE_ACCESS_TOKEN',
          payload: customerAccessToken
        });
        dispatch(getCheckOutId())
      }else{
        const errors = response.data.customerAccessTokenCreate.userErrors.map(error => error.message);
        Alert.alert('Error', errors.join(', '))

        dispatch({
          type: 'STORE_ACCESS_TOKEN',
          payload: 'FAILURE'
        });
        
      }
    });
  };
}

export const register = (input,callback) => {
  return async dispatch => {
    axios({
      url: graphqlApiUrl,
      method: 'post',
      headers: {
        'X-Shopify-Storefront-Access-Token': storefrontAccessToken
      },
      data: {
        query: `
          mutation customerCreate($input: CustomerCreateInput!) {
            customerCreate(input: $input) {
              userErrors {
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
          input
        }
      }
    }).then(result => {
      const response = result.data;
      const customerId = response?.data?.customerCreate?.customer?.id;

      if(customerId){
        const credentials = {
          email: input.email,
          password: input.password
        }
        // callback("sucess")
        dispatch(login(credentials));
        
      }else{
        callback("error")
        console.log('response error-->', JSON.stringify(response));
        const errors = response.data.customerCreate && response.data.customerCreate.userErrors.map(error => error.message) || response.errors.map(error => error.message);
        Alert.alert('Error', errors.join(', '))
      }
    });
  };
}

export const forgotPassword = email => {
  return async dispatch => {
    axios({
      url: graphqlApiUrl,
      method: 'post',
      headers: {
        'X-Shopify-Storefront-Access-Token': storefrontAccessToken
      },
      data: {
        query: `
          mutation customerRecover($email: String!) {
            customerRecover(email: $email) {
              customerUserErrors {
                code
                field
                message
              }
            }
          }
        `,
        variables: {
          email
        }
      }
    }).then(result => {
      const response = result.data;
      const errors = response?.data?.errors;
      const customerUserErrors = response?.data?.customerRecover?.customerUserErrors;

      if((errors && errors.length) || (customerUserErrors && customerUserErrors.length)){
        const errorMessages = !!errors ? errors.map(error => error.message) : customerUserErrors.map(error => error.message);

        dispatch({
          type: 'SET_FORGOT_PASSWORD_STATUS',
          payload: errorMessages.join(', ')
        });
      }else{
        dispatch({
          type: 'SET_FORGOT_PASSWORD_STATUS',
          payload: true
        });
      }
    });
  };
}

export const unsetAllUserData = () => {
	return async dispatch => {
    await AsyncStorage.clear();

		dispatch({
			type: 'RESET_USER_STATE',
			payload: null
		});

		dispatch({
			type: 'RESET_FINGER_PRINTS_STATE',
			payload: null
		});

		dispatch({
			type: 'RESET_PRODUCTS_STATE',
			payload: null
		});

		dispatch({
			type: 'RESET_ORDERS_STATE',
			payload: null
		});
	}
}

export const storeCustomerAccessToken = token => {
	return {
    type: 'STORE_ACCESS_TOKEN',
    payload: token
  };
}
export const resetForgotPasswordStatus = () => {
	return {
    type: 'SET_FORGOT_PASSWORD_STATUS',
    payload: null
  };
}

export const setRememberMeData = rememberMeData => ({
  type: 'REMEMBER_ME',
  payload: rememberMeData
});