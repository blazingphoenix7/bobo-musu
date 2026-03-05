import { createStackNavigator } from 'react-navigation-stack';

import TakeFingerPrint from './TakeFingerPrint';
import PreviewFingerPrint from './PreviewFingerPrint';
import RequestFingerPrint from './RequestFingerPrint';
import SingleFingerPrint from './SingleFingerPrint';
import FingerPrintVault from './FingerPrintVault';
import FingerprintRequests from './FingerprintRequests';
import Tutorial from './Tutorial';
import FingerprintDetail from './FingerprintDetail';
import ConfirmationProduct from '../Products/ConfirmationProduct';

export default AuthNavigator = createStackNavigator(
  {
    TakeFingerPrint: {screen: TakeFingerPrint},
    PreviewFingerPrint: {screen: PreviewFingerPrint},
    RequestFingerPrint: {screen: RequestFingerPrint},
    SingleFingerPrint: {screen: SingleFingerPrint},
    FingerPrintVault: {screen: FingerPrintVault},
    FingerprintRequests: {screen: FingerprintRequests},
    Tutorial: {screen: Tutorial},
    FingerprintDetail: {screen: FingerprintDetail},
    ConfirmationProduct: {screen: ConfirmationProduct}
  },
  {
    initialRouteName: 'TakeFingerPrint',
    headerMode: 'none'
  }
);