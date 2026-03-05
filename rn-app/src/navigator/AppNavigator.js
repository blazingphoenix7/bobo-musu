import { createAppContainer } from 'react-navigation';
import {createDrawerNavigator} from 'react-navigation-drawer';

import SideMenu from './SideMenu';
import Splash from '../screens/Splash';
import AuthNavigator from '../screens/Auth';
import Products from '../screens/Products';
import FingerPrints from '../screens/FingerPrints';
import User from '../screens/User';

// console.disableYellowBox = true;

const AppNavigator = {
//   Splash: {screen: Splash},
//   Auth: {screen: AuthNavigator},
  Products: {screen: Products},
  FingerPrints: {screen: FingerPrints},
  User: {screen: User},
};

const DrawerAppNavigator = createDrawerNavigator(
  {
    ...AppNavigator,
  },
  {
    contentComponent: SideMenu,
    initialRouteName: 'Products',
  },
);

const AppContainer = createAppContainer(DrawerAppNavigator);

export default AppContainer;