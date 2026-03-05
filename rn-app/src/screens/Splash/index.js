import { createStackNavigator } from 'react-navigation-stack';

import Splash from './Splash';

export default AuthNavigator = createStackNavigator(
  {
    Splash: {screen: Splash}
  },
  {
    initialRouteName: 'Splash',
    headerMode: 'none'
  }
);