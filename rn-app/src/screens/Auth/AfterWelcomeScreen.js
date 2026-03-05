import React from 'react';
import {SafeAreaView, TextInput, Image, ImageBackground, View, Text, TouchableOpacity, ScrollView, Alert, ActivityIndicator} from 'react-native';
import { connect } from 'react-redux';
import { NavigationActions, StackActions } from 'react-navigation';

import styles from './styles';
import {setShouldSkip} from '../../actions/general';

class AfterWelcomeScreen extends React.Component {

    constructor(props){
        super(props);
        this.state = {
        }
    }
  
    componentDidUpdate(){
        
    }

    handleSignup = () => {
        this.props.navigation.navigate("Register")
    }

    handleSignIn = () => {
        this.props.navigation.navigate("Login")
    }

    handleSignGuest = () => {
        this.props.setShouldSkip();
        this.props.navigation.navigate('Collections');
    }

    render(){
        
        const {navigation} = this.props;

        return (
            <ImageBackground style={styles.container} source={require('../../assets/images/bg.png')} resizeMode={'cover'}>
                <SafeAreaView style={[styles.innerContainer,{justifyContent:'space-around'}]}>
                    <Image source={require('../../assets/images/logo.png')} style={[styles.logo]} />
                    <View style={{marginBottom: 30}}>
                        <View style={{flexDirection:'row', marginHorizontal:20}}>
                            <TouchableOpacity style={[styles.primaryButton,{marginRight:10, flex:1}]} onPress={this.handleSignup} >
                                <Text style={[styles.primaryButtonText,{fontWeight:'bold'}]}>Sign up</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={[styles.primaryButton,{marginLeft:10, flex:1}]} onPress={this.handleSignIn} >
                                <Text style={[styles.primaryButtonText,{fontWeight:'bold'}]}>Login</Text>
                            </TouchableOpacity>
                        </View>
                        <TouchableOpacity style={[styles.skipButton, styles.continueAsGuestButton ]} onPress={this.handleSignGuest} >
                            <Text style={[styles.skipButtonText, styles.continueAsGuestButtonText]}>Continue as a guest</Text>
                        </TouchableOpacity>
                    </View>
                    
            
                </SafeAreaView>
            </ImageBackground>
        )
    }
}

const mapDispatchToProps = dispatch => ({
    setShouldSkip: () => dispatch(setShouldSkip()),
});

const mapStateToProps = state => ({
    
});

export default connect(mapStateToProps, mapDispatchToProps)(AfterWelcomeScreen);