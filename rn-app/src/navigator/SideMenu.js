import React from 'react';
import {TouchableOpacity, View, ScrollView, SafeAreaView, Image, StyleSheet, Text} from 'react-native';
import {connect} from 'react-redux';
import { StackActions, NavigationActions } from 'react-navigation';
// import Icon from 'react-native-vector-icons/FontAwesome';
import { XIcon} from '../components/icons';
import * as Colors from '../styles/colors';
import {unsetAllUserData} from '../actions/auth';

class SideMenu extends React.Component {
  constructor(props){
    super(props);

    this.state = {
      isLoggedIn: false,
    }

    this.currentRouteName = null;
  }

  logout = () => {
    this.props.navigation.closeDrawer();
    this.props.navigation.navigate('Auth');
    this.props.unsetAllUserData();
  }

  onMenuItemPressed = item => {
    if(item.access_route){
      this.props.navigation.closeDrawer();
      this.props.navigation.navigate(item.access_route);
      
    }else if(item.method){
      if(!!this[item.method]){
        this[item.method]();
      }
    }
  };

  renderMenuItem = item => (
    (item.registered_user_only && this.state.isLoggedIn) || (!item.registered_user_only && !this.state.isLoggedIn) || (item.name === 'shop') ? (<TouchableOpacity
      style={styles.container}
      key={`${item.name}--blueprint-button`}
      activeOpacity={1}
      onPress={() => this.onMenuItemPressed(item)}>
      <View style={styles.content}>
        <View style={styles.content}>
          {/* <Icon
            style={styles.icon}
            name={item.icon_name ? item.icon_name : 'pencil-square-o'}
            size={24}
            color="#F88087"
          /> */}
          <Text style={[styles.text, {color:'#878181',fontWeight: item.access_route === this.currentRouteName ? 'bold' : 'normal'}]}>{item.human_name.toUpperCase()}</Text>
        </View>
        {/* <Icon
          name="chevron-right"
          size={24}
          color="#F88087"
        /> */}
      </View>
    </TouchableOpacity>) : <View key={`${item.name}-button`} />
  );

  componentDidUpdate(){
    const navigationState = this.props.navigation.state;
    const currentRouteGroup = navigationState.routes[navigationState.index];
    const currentRoute = currentRouteGroup.routes[currentRouteGroup.index];

    this.currentRouteName = currentRoute && currentRoute.routeName;

    const {customerDetails} = this.props.user;

    if(!!customerDetails && !this.state.isLoggedIn){
      this.setState({isLoggedIn: true});
    }else if(!customerDetails && this.state.isLoggedIn){
      this.setState({isLoggedIn: false});
    }
  }

  render() {
    const {sidemenuRoutes} = this.props.general;
    console.log('isLoggedIn-->',this.state.isLoggedIn)

    return (
      <SafeAreaView style={styles.wrapper}>
        <ScrollView showsVerticalScrollIndicator={false}>
          <View style={[styles.content, styles.logoWrap]}>
            <View style={{width:50}} />
            <Image source={require('../assets/images/logo-row.png')} style={styles.logo} />
            <TouchableOpacity style={{width:50, alignItems:'center', justifyContent:'center'}} onPress={() => this.props.navigation.closeDrawer()}>
					    <XIcon fill={Colors.primaryTextColor} />
				    </TouchableOpacity>
          </View>
          
          {sidemenuRoutes.map(this.renderMenuItem)}
        </ScrollView>
      </SafeAreaView>
    );
  }
}

const styles = StyleSheet.create({
  wrapper: {
    flex: 1,
  },
  container: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomColor: Colors.grayishBorderColor,
    borderBottomWidth: 0,
  },
  content: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  logoWrap: {
    flexDirection:'row',
    alignItems:'center',
    justifyContent: 'center',
    marginTop: 30,
    marginBottom: 10,
  },
  logo: {
    width: 232 * 0.7,
    height: 66 * 0.7,
  },
  icon: {
    marginRight: 13,
  },
  text: {
    textAlign: 'left',
    fontFamily: 'Avenir',
    fontSize: 16,
    lineHeight: 24,
    letterSpacing: 0.26,
    color: Colors.darkColor,
  },
});

const mapDispatchToProps = dispatch => ({
	unsetAllUserData: () => dispatch(unsetAllUserData()),
});

const mapStateToProps = state => ({
  general: state.general,
  user: state.user
});

export default connect(mapStateToProps, mapDispatchToProps)(SideMenu);