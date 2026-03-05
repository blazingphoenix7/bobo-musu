import {createStore, combineReducers, applyMiddleware, compose } from "redux";
import ReduxThunk from 'redux-thunk';
import { persistStore, persistReducer } from 'redux-persist'
import autoMergeLevel2 from 'redux-persist/lib/stateReconciler/autoMergeLevel2'
import AsyncStorage from '@react-native-community/async-storage';
import { createFilter, createBlacklistFilter, createWhitelistFilter } from 'redux-persist-transform-filter';

// this app uses React Native Debugger, but it works without it
const composeEnhancers = window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ || compose;
const middlewares = [ReduxThunk];

import general from './general';
import products from './products';
import orders from './orders';
import fingerprints from './fingerprints';
import user from './user';

// you want to remove some keys before you save
const userWhiteListFilter = createWhitelistFilter(
  'user',
  ['customerDetails', 'customerAccessToken','forgotPasswordStatus', 'isUserFirstTime','rememberMeData']
);


const persistConfig = {
  key: 'root',
  transforms: [userWhiteListFilter],
  storage: AsyncStorage,
  stateReconciler: autoMergeLevel2
}

export const persistedReducer = persistReducer(persistConfig, combineReducers({
  general,
  products,
  orders,
  fingerprints,
  user
}));

const rootStore = createStore(persistedReducer, applyMiddleware(...middlewares));
export const persistor = persistStore(rootStore);
export const store = rootStore;
