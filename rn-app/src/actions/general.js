import axios from 'axios';
import AsyncStorage from '@react-native-community/async-storage';

import {apiUrl} from '../constants';

export const loadSidebarMenuRoutes = () => {
	return async dispatch => {
    const customerAccessToken = await AsyncStorage.getItem('accessToken');
		axios.get(`${apiUrl}/shopify/sidebar-menu/`, {
      headers: {
        'STOREFRONT-CUSTOMER-ACCESS-TOKEN': customerAccessToken
      }
    })
    .then(res => {
      if (res.status === 200) {
        dispatch({
          type: 'LOADED_SIDEBAR_MENU_ROUTES',
          payload: res.data,
        });
      }
    })
    .catch(err => console.log('ERROR Loading Sidebar Menu', err));
	};
}

export const loadHomeSliders = () => {
	return async dispatch => {
    const customerAccessToken = await AsyncStorage.getItem('accessToken');

		axios.get(`${apiUrl}/homepage-sliders/`, {
      headers: {
        'STOREFRONT-CUSTOMER-ACCESS-TOKEN': customerAccessToken
      }
    })
    .then(res => {
      if (res.status === 200) {
        dispatch({
          type: 'LOADED_HOME_SLIDERS',
          payload: res.data,
        });
      }
    })
    .catch(err => console.log('ERROR Loading Home Sliders', err));
	};
}

export const toastSuccess = message => ({
	type: 'RECEIVE_TOAST',
	payload: {
		type: 'success',
		title: 'Success!',
		message
	}
});

export const toastError = message => ({
	type: 'RECEIVE_TOAST',
	payload: {
		type: 'error',
		title: 'Error!',
		message
	}
});

export const resetToast = () => {
	return {
		type: 'RECEIVE_TOAST',
		payload: {}
	}
}

export const setShouldSkip = () => {
	return async dispatch => {
    await AsyncStorage.setItem('shouldSkip', 'true');

    dispatch({
      type: 'SET_SHOULD_SKIP',
      payload: {}
    });
  }
}