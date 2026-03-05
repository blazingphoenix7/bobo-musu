import { createStackNavigator } from 'react-navigation-stack';

import Collections from './Collections';
import Catalog from './Catalog';
import Product from './Product';
import ConfirmationProduct from './ConfirmationProduct';
import Checkout from './Checkout';
import MyOrders from './MyOrders';
import Favorites from './Favorites';
import ProductDetails from './ProductDetails';

import TakeFingerPrint from '../FingerPrints/TakeFingerPrint';
import PreviewFingerPrint from '../FingerPrints/PreviewFingerPrint';
import FingerPrintVault from '../FingerPrints/FingerPrintVault';
import FingerprintDetail from '../FingerPrints/FingerprintDetail';
import Tutorial from '../FingerPrints/Tutorial';
import SingleFingerPrint from '../FingerPrints/SingleFingerPrint';

export default CategoryNavigator = createStackNavigator(
  {
    Collections: {screen: Collections},
    Catalog: {screen: Catalog},
    Product: {screen: Product},
    Checkout: {screen: Checkout},
    MyOrders: {screen: MyOrders},
    Favorites: {screen: Favorites},
    ProductDetails: {screen: ProductDetails},
    TakeFingerPrint: {screen: TakeFingerPrint},
    PreviewFingerPrint: {screen: PreviewFingerPrint},
    FingerPrintVault: {screen: FingerPrintVault},
    FingerprintDetail: {screen: FingerprintDetail},
    Tutorial: {screen: Tutorial},
    SingleFingerPrint: {screen: SingleFingerPrint},
    ConfirmationProduct: {screen: ConfirmationProduct},
  },
  {
    initialRouteName: 'Collections',
    headerMode: 'none'
  }
);