import { createAppContainer, createSwitchNavigator } from 'react-navigation';

import AppNavigator  from './AppNavigator';
import AuthNavigator from '../screens/Auth';
import Splash from '../screens/Splash';
// console.disableYellowBox = true;


const Navigator = createSwitchNavigator(
  {
    Splash: {screen: Splash},
    App : {screen : AppNavigator},
    Auth : {screen : AuthNavigator},
  },
  {
    initialRouteName: 'Splash',
  },
);

const AppContainer = createAppContainer(Navigator);

export default AppContainer;