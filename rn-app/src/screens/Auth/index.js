import { createStackNavigator } from "react-navigation-stack";

import Login from "./Login";
import Register from "./Register";
import ForgotPassword from "./ForgotPassword";
import WelcomeScreen from "./WelcomeScreen";
import AfterWelcomeScreen from "./AfterWelcomeScreen";

export default AuthNavigator = createStackNavigator(
  {
    Login: {screen: Login},
    Register: {screen: Register},
    ForgotPassword: {screen: ForgotPassword},
    WelcomeScreen: {screen: WelcomeScreen},
    AfterWelcomeScreen: {screen: AfterWelcomeScreen},
  },
  {
    // initialRouteName: "Login",
    initialRouteName: "WelcomeScreen",
    headerMode: 'none',
    navigationOptions: {
      drawerLockMode: 'locked-closed'
    }
  }
);