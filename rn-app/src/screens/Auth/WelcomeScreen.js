import React from 'react';
import {SafeAreaView, TextInput, Image, ImageBackground, 
    View, Text, TouchableOpacity, ScrollView, Alert, ActivityIndicator, Dimensions} from 'react-native';
import { connect } from 'react-redux';
import { NavigationActions, StackActions } from 'react-navigation';

import styles from './styles';
import Swiper from 'react-native-swiper'
import {CheckboxOffIcon, CheckboxOnIcon, EyeIcon} from "../../components/icons";
import {login, storeCustomerAccessToken} from '../../actions/auth';
import {loadCustomerDetails} from '../../actions/user';
import {setShouldSkip} from '../../actions/general';
import { Colors } from 'react-native/Libraries/NewAppScreen';
const {width: deviceWidth, height: deviceHeight} = Dimensions.get('window')

class WelcomeScreen extends React.Component {

    constructor(props){
        super(props);
        this.state = {
            currentIndex:0,
            welcomeScreenData : [
                {
                    title : "Select an Item",
                    description: "Browse and choose your personalized piece of jewelry",
                    image: require('../../assets/images/welcome-screen-icon1.png')
                },
                {
                    title : "Take your fingerprint",
                    description: "Take a photo of your fingerprint, choose an existing print from the print vault, or request a print from someone else.",
                    image: require('../../assets/images/welcome-screen-icon2.png')
                },
                {
                    title : "Complete your order",
                    description: "Confirm your purchase with your shipping and payment information",
                    image: require('../../assets/images/welcome-screen-icon3.png')
                }
            ]
        }
        if(!props.isUserFirstTime) {
            
            const resetAction = StackActions.reset({
                index: 0,
                actions: [NavigationActions.navigate({ routeName: 'AfterWelcomeScreen' })],
            });
            this.props.navigation.dispatch(resetAction);
        }
    }
  
    componentDidUpdate(){
        
    }

    handleSkip = () => {
        this.props.setIsUserFirstTime(false);
        const resetAction = StackActions.reset({
            index: 0,
            actions: [NavigationActions.navigate({ routeName: 'AfterWelcomeScreen' })],
        });
        this.props.navigation.dispatch(resetAction);
    }

    render(){
        
        const {navigation} = this.props;

        return (
            <ImageBackground style={styles.container} source={require('../../assets/images/bg.png')} resizeMode={'cover'}>
                <SafeAreaView style={styles.innerContainer}>
                    <Image source={require('../../assets/images/logo-row.png')} style={[styles.logo]} />
                    <View style={styles.welcomeMiddleContainer}>
                        <Swiper 
                            containerStyle={styles.welcomeSlider}
                            loop={false}
                            paginationStyle={styles.paginationStyle} 
                            activeDotColor={Colors.labelColor} 
                            activeDotStyle={styles.activeDotStyle} 
                            dotStyle={styles.dotStyle}
                            onIndexChanged={(index) => this.setState({ currentIndex : index})}
                            >
                            {this.state.welcomeScreenData.map((data, index) =>{
                                return(
                                    <View style={{alignItems:'center', justifyContent:'space-around', marginHorizontal:20, flex:1}} key={index}>
                                        <Text style={styles.welcomeTitle}>{data.title}</Text>
                                        <View style={{flex:1}}>
                                            <Image source={data.image} style={[styles.welcomeImage,{height: index == 1 ? deviceHeight * .25 : deviceHeight * .28, }]} resizeMode={'contain'} />
                                        </View>
                                        <View style={{flex:0.25}}>
                                            <Text style={styles.welcomeDescription}>{data.description}</Text>
                                        </View>
                                    </View>
                                )
                            })}
                        </Swiper>
                    </View>
                    <View style={{marginBottom: 30}}>
                        {this.state.currentIndex == 2 ?

                            <TouchableOpacity style={[styles.primaryButton,{marginHorizontal: 30,}]} onPress={this.handleSkip} >
                                <Text style={[styles.primaryButtonText]}>Let's get started!</Text>
                            </TouchableOpacity>
                        :
                        <TouchableOpacity style={[styles.skipButton]} onPress={this.handleSkip} >
                            <Text style={[styles.skipButtonText]}>Skip</Text>
                        </TouchableOpacity>}
                    </View>
                    
            
                </SafeAreaView>
            </ImageBackground>
        )
    }
}

const mapDispatchToProps = dispatch => ({
	setIsUserFirstTime : (props) => dispatch({
        type: 'IS_USER_FIRST_TIME',
        payload: props
    })
});

const mapStateToProps = state => ({
    isUserFirstTime : state.user.isUserFirstTime
});

export default connect(mapStateToProps, mapDispatchToProps)(WelcomeScreen);