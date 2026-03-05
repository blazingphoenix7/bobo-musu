import React from "react";
import {StyleSheet, ImageBackground, SafeAreaView, Image, Platform} from "react-native";
import AsyncStorage from '@react-native-community/async-storage';
import moment from 'moment';
import {connect} from 'react-redux';
import {Notifications} from 'react-native-notifications';
import SplashScreen from 'react-native-splash-screen';

import {storeCustomerAccessToken} from '../../actions/auth';
import {loadCustomerDetails, registerNotificationsToken} from '../../actions/user';

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    width: '100%',
    alignItems: 'center',
    justifyContent: 'center'
  },
  logo: {
		width: 252,
		height: 162
  },
});

class Splash extends React.Component {
  constructor(props){
		super(props);

		this.registerDevice();
		this.registerNotificationEvents();
  }
  
  registerNotificationEvents = () => {
		// Notification while app is in Foreground
		Notifications.events().registerNotificationReceivedForeground((notification, completion) => {
			console.log('Notification Received - Foreground', notification);

			this.handleNotification(notification.payload, 'foreground');

			// Calling completion on iOS with `alert: true` will present the native iOS inApp notification.
			completion({ alert: true, sound: true, badge: false });
		});

		// When user open from notification sent while app is Closed
		Notifications.events().registerNotificationOpened((notification, completion) => {
			console.log('Notification opened by device user', notification);
			console.log(`Notification opened with an action identifier: ${notification.identifier}`);

			if(Platform.OS === 'ios'){
				Notifications.ios.setBadgeCount(0);
			}

			this.handleNotification(notification.payload, 'closed');
			completion();
		});

		// Notification while app is in Background
		Notifications.events().registerNotificationReceivedBackground((notification, completion) => {
			console.log('Notification Received - Background', notification);

			this.handleNotification(notification.payload, 'background');

			// Calling completion on iOS with `alert: true` will present the native iOS inApp notification.
			completion({ alert: true, sound: true, badge: true });
		});

		if (Platform.OS === 'android') {
			Notifications.getInitialNotification()
			.then(notification => {
				console.log('Initial notification was:', notification || 'N/A');

				if(notification){
					this.handleNotification(notification.payload);
				}
			})
			.catch(err => console.log('getInitialNotifiation() failed', err));
		}
  }
  
  handleNotification = async (notificationPayload, appState) => {
		if(notificationPayload){
			// go to a screen
			if(notificationPayload.screen){
				const navigationParams = notificationPayload.navigationParams;
				const params = navigationParams ? JSON.parse(navigationParams) : null;

				if(appState === 'foreground'){
					Alert.alert(
						notificationPayload.title,
						notificationPayload.body,
						[
							{
								text: 'Cancel',
								style: 'cancel',
							},
							{
								text: 'Go',
								style: 'default',
								onPress: () => this.props.navigation.navigate(notificationPayload.screen, params)
							},
						],
						{ cancelable: true }
					);
				}else{
					this.notificationToScreen = {
						screen: notificationPayload.screen,
						params
					};
				}
			}
		}
	}

  async componentDidMount() {
    const accessToken = await AsyncStorage.getItem('accessToken');
    const accessTokenExpiration = await AsyncStorage.getItem('accessTokenExpiration');

    SplashScreen.hide();

		if(!!accessToken && moment(accessTokenExpiration).isAfter(moment())){
      this.props.loadCustomerDetails();

      this.props.storeCustomerAccessToken({
        accessToken,
        expiresAt: accessTokenExpiration
      });

      this.props.navigation.navigate('App');
    }else{
			const shouldSkip = await AsyncStorage.getItem('shouldSkip');

			if(!!shouldSkip){
				this.props.navigation.navigate('App');
			}else{
				this.props.navigation.navigate('Auth');
			}
    }
  }

	registerDevice = () => {
		Notifications.events().registerRemoteNotificationsRegistered(event => {
      console.log('Device Token Received', event.deviceToken);

      this.props.registerNotificationsToken(event.deviceToken);
		});

		Notifications.events().registerRemoteNotificationsRegistrationFailed(event => {
			console.log('Error', event);
		});
				
		Notifications.registerRemoteNotifications();
	}

  render() {
    return (<SafeAreaView style={styles.container}>
      <Image source={require('../../assets/images/logo.png')} style={styles.logo} />
		</SafeAreaView>);
  }
}

const mapDispatchToProps = dispatch => ({
	loadCustomerDetails: () => dispatch(loadCustomerDetails()),
	storeCustomerAccessToken: token => dispatch(storeCustomerAccessToken(token)),
	registerNotificationsToken: deviceToken => dispatch(registerNotificationsToken(deviceToken)),
});

const mapStateToProps = state => ({
  user: state.user,
});

export default connect(mapStateToProps, mapDispatchToProps)(Splash);