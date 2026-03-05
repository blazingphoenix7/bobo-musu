import React from 'react';
import {SafeAreaView, TextInput, Image, ImageBackground, View, Text, TouchableOpacity, ScrollView, Alert, ActivityIndicator} from 'react-native';
import { Container, Content } from 'native-base';
import { connect } from 'react-redux';
import { StackActions, NavigationActions } from 'react-navigation';
import styles from './styles';
import {CheckboxOffIcon, CheckboxOnIcon, EyeIcon} from "../../components/icons";
import {login, storeCustomerAccessToken, setRememberMeData} from '../../actions/auth';
import {loadCustomerDetails} from '../../actions/user';
import {setShouldSkip} from '../../actions/general';
import {validateEmail, validatePassword} from '../../helpers';

class Login extends React.Component {

  constructor(props){
    super(props);
    this.state = {
      loading: false,
      rememberMe: props.rememberMeData != undefined,
      hidePassword: true,
      email: props.rememberMeData && props.rememberMeData.email || '' ,
      password: props.rememberMeData && props.rememberMeData.password || ''
    }
  }
  

  handleRememberMe = () => this.setState({rememberMe: !this.state.rememberMe});
  handlePasswordVisibility = () => this.setState({hidePassword: !this.state.hidePassword});
  setValue = (field, value) => this.setState({[field]: value});

  handleLogin = () => {
    const {email, password, rememberMe} = this.state;

    if(!!email && !!password){
		this.setState({loading: true});
		this.props.login({email, password});
		this.props.setRememberMeData(rememberMe ? {email, password} : undefined);
    }else{
      Alert.alert('Missing Values', 'Please enter your credentials!')
    }
  }

  handleSkipButton = () => {
    this.props.setShouldSkip();
    this.props.navigation.navigate('Collections');
  }

  componentDidUpdate(){
    const {customerAccessToken} = this.props.user;

    if(this.state.loading && customerAccessToken !== null){
      if(customerAccessToken === 'FAILURE'){
        this.props.storeCustomerAccessToken(null);

        this.setState({loading: false});
      }else{
        this.props.loadCustomerDetails();

        this.setState({loading: false});
        this.props.navigation.navigate('App');
    
      }
    }
  }

  render(){
    const {loading, rememberMe, hidePassword, email, password} = this.state;
    const {navigation} = this.props;

    return (
		<Container>
			<ImageBackground style={styles.container} source={require('../../assets/images/bg.png')}>
					<TouchableOpacity 
							style={{position:'absolute', top: 40, left: 15, zIndex:1}}
							onPress={() => this.props.navigation.goBack()} 
						>
							<Image 
								source={require('../../assets/icons/left-arrow.png')} 
								style={{height:20, width: 30}}
								resizeMode={'contain'}
							/>
					</TouchableOpacity>
						
					<Content>
						
					<Image source={require('../../assets/images/logo.png')} style={styles.logo} />
						<View style={styles.inputFieldsWrap}>
							<Text style={styles.inputFieldLabel}>Please Sign in here:</Text>
							<TextInput
							style={styles.inputField}
							value={email}
							placeholder="Email"
							keyboardType="email-address"
							textContentType="emailAddress"
							onChangeText={value => this.setValue('email', value)}
							autoCompleteType="email"
							// caretHidden={true}
							autoCapitalize='none'
							autoCorrect={false}
							/>
							<View style={{marginVertical: 20}}>
							<TextInput
								style={styles.inputField}
								value={password}
								placeholder="Password"
								textContentType="password"
								secureTextEntry={hidePassword}
								onChangeText={value => this.setValue('password', value)}
							/>
							<TouchableOpacity onPress={this.handlePasswordVisibility} style={{position: 'absolute', right: 16, top: 7}}>
								<EyeIcon />
							</TouchableOpacity>
							</View>

							<TouchableOpacity onPress={this.handleRememberMe} style={styles.checkboxWrap}>
							{rememberMe ? <CheckboxOnIcon /> : <CheckboxOffIcon />}
							<Text style={styles.checkboxText}>Remember Me</Text>
							</TouchableOpacity>
						</View>

						<TouchableOpacity style={[styles.primaryButton, {justifyContent: 'center', flexDirection: 'row', marginHorizontal:50, marginTop:10}]} onPress={this.handleLogin} disabled={loading}>
							{!!loading && <ActivityIndicator />}
							<Text style={[styles.primaryButtonText, {marginLeft: 10}]}>Sign In</Text>
						</TouchableOpacity>
				

						<TouchableOpacity onPress={() => navigation.navigate('ForgotPassword')}>
							<Text style={styles.forgotPassword}>Forgot Password?</Text>
						</TouchableOpacity>

						<View style={styles.footer}>
							<Text style={styles.footerTitle}>or</Text>
							<TouchableOpacity onPress={() => navigation.navigate('Register')}>
							<Text style={styles.footerSubtitle}>Create an Account</Text>
							</TouchableOpacity>
						</View>
						</Content>
				</ImageBackground>
			</Container>
		)
  	}
}

const mapDispatchToProps = dispatch => ({
	setShouldSkip: () => dispatch(setShouldSkip()),
	login: credentials => dispatch(login(credentials)),
	loadCustomerDetails: () => dispatch(loadCustomerDetails()),
	storeCustomerAccessToken: token => dispatch(storeCustomerAccessToken(token)),
	setRememberMeData: (props) => dispatch(setRememberMeData(props)),
});

const mapStateToProps = state => ({
  user: state.user,
  rememberMeData: state.user.rememberMeData,
});

export default connect(mapStateToProps, mapDispatchToProps)(Login);