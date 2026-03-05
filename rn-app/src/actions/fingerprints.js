import axios from 'axios';
import AsyncStorage from '@react-native-community/async-storage';
import {captureException} from '@sentry/react-native';
import {apiUrl} from '../constants';
import {toastError} from './general';
import {setProductAssignPrint} from '../actions/products';
import RNFetchBlob from 'rn-fetch-blob'

export const loadFingerPrintRequests = customerId => {
	return async dispatch => {
    const customerAccessToken = await AsyncStorage.getItem('accessToken');

		axios.get(`${apiUrl}/fingerprint-request/list/${customerId}/`, {
      headers: {
        'STOREFRONT-CUSTOMER-ACCESS-TOKEN': customerAccessToken
      }
    })
    .then(res => {
      if (res.status === 200) {
        dispatch({
          type: 'LOADED_FINGER_PRINT_REQUESTS',
          payload: res.data,
        });
      }
    })
    .catch(err => console.log('ERROR', err));
	};
}

export const sendFingerPrintRequest = params => {
	return async dispatch => {
    const customerAccessToken = await AsyncStorage.getItem('accessToken');

		axios.post(`${apiUrl}/fingerprint-request/send-request/`, params, {
      headers: {
        'STOREFRONT-CUSTOMER-ACCESS-TOKEN': customerAccessToken
      }
    })
    .then(res => {
      if (res.status ===200) {
        dispatch({
          type: 'NEW_FINGER_PRINT_REQUEST',
          payload: res.data
        });
      }
    })
    .catch(err => console.log('ERROR', err));
	};
}


export const setTakenFingerPrintPhoto = takenPhoto => {
	return {
    type: 'SET_TAKEN_FINGER_PRINT_PHOTO',
    payload: takenPhoto
  };
}

export const loadFingerPrints = () => {
	return async dispatch => {
    const customerAccessToken = await AsyncStorage.getItem('accessToken');

		axios.get(`${apiUrl}/shopify/customers/fingerprints/`, {
      headers: {
        'STOREFRONT-CUSTOMER-ACCESS-TOKEN': customerAccessToken,
      }
    })
    .then(res => {
      if (res.status === 200) {
        console.log('loadFingerPrints-->', JSON.stringify(res.data));
        dispatch({
          type: 'LOADED_FINGER_PRINTS',
          payload: res.data,
        });
      }
    })
    .catch(err => console.log('ERROR', err));
	};
}

export const deleteFingerPrint = (id, index) => {
	return async (dispatch,getState) => {
    const customerAccessToken = await AsyncStorage.getItem('accessToken');
    const state = getState();
    let {userFingerprints} = state.fingerprints;
    
		axios.delete(`${apiUrl}/shopify/customers/fingerprints/${id}/`, {
      headers: {
        'STOREFRONT-CUSTOMER-ACCESS-TOKEN': customerAccessToken,
      }
    })
    .then(res => {
      console.log('deleteFingerPrint res-->', JSON.stringify(res));
      if (res.status === 200) {
        console.log('deleteFingerPrint-->', JSON.stringify(res.data));
        
        userFingerprints.splice(index,1);
        
        dispatch({
          type: 'LOADED_FINGER_PRINTS',
          payload: {results : [...userFingerprints]},
        });
        
      }
    })
    .catch(err => console.log('ERROR', err));
	};
}

export const addNewFingerPrint = (fingerprintName, fingerprintPhoto, callback) => {
	return async dispatch => {
    const customerAccessToken = await AsyncStorage.getItem('accessToken');

    // let formData = new FormData();
    // formData.append('fingerprint_title',fingerprintName)
    // formData.append('fingerprint_file',{
    //   uri: fingerprintPhoto,
    //   type: 'image/jpeg',
    //   name: new Date().getTime()
    // })
    let postData = [
      { name : 'fingerprint_title', data : fingerprintName},
      { name : 'fingerprint_file', filename : new Date().getTime()+'', type:'image/jpeg', data: RNFetchBlob.wrap(decodeURIComponent(Platform.OS === 'ios' ? fingerprintPhoto.replace('file://', '') : fingerprintPhoto))},
    ]
    console.log('postData-->',JSON.stringify(postData));
    RNFetchBlob.fetch('POST', `${apiUrl}/shopify/customers/add-fingerprint/`, {
      'STOREFRONT-CUSTOMER-ACCESS-TOKEN': customerAccessToken,
      'Content-Type' : 'multipart/form-data',
    },postData).then((resp) => {
      console.log('resp-->', resp.data)
      console.log('typeof resp-->', typeof resp.data)
            dispatch({
              type: 'ADDED_FINGER_PRINT',
              payload: JSON.parse(resp.data),
            });
        callback(JSON.parse(resp.data));
        dispatch(loadFingerPrints())
        
    }).catch((err) => {
      console.log('err-->', JSON.stringify(err))
      console.log('err1-->', err)
    })
    
  //   var fileType = fingerprintPhoto.split('.').pop();
  //   let formData = new FormData();
  //   formData.append('fingerprint_title',fingerprintName)
  //   formData.append('fingerprint_file',{
  //     uri: fingerprintPhoto,
  //     type: 'image/jpeg',
  //     name: new Date().getTime()
  //   })

  //   // {
  //   //   fingerprint_title: fingerprintName,
  //   //   fingerprint_file: fingerprintPhoto
  //   // }
	// 	axios.post(`${apiUrl}/shopify/customers/add-fingerprint/`, formData, {
  //     headers: {
  //       'STOREFRONT-CUSTOMER-ACCESS-TOKEN': customerAccessToken,
  //       "Content-Type": "multipart/form-data",
  //     }
  //   })
  //   .then(res => {
  //     console.log('add-fingerprint res', JSON.stringify(res));
  //     if (res.status === 200) {
  //       dispatch({
  //         type: 'ADDED_FINGER_PRINT',
  //         payload: res.data,
  //       });
  //       callback(res.data)
  //     }
  //   })
  //   .catch(err => {
  //     console.log('ERROR', err);
  //     console.log('ERROR data', JSON.stringify(err));
  //     callback(false)
  //     captureException(err);
  //   });
	};
}

export const setActiveFingerprintId = fingerprintId => ({
  type: 'SET_ACTIVE_FINGER_PRINT_ID',
  payload: fingerprintId
})