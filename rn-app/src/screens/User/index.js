import { createStackNavigator } from "react-navigation-stack";

import MyAccount from "./MyAccount";

export default AuthNavigator = createStackNavigator(
  {
    MyAccount: {screen: MyAccount},
  },
  {
    initialRouteName: "MyAccount",
    headerMode: 'none'
  }
);