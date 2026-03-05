import React from 'react';
import {SafeAreaView, TextInput, Image, ImageBackground, View, Text, TouchableOpacity, Alert, ScrollView, Keyboard, ActivityIndicator} from 'react-native';
import {Container, Content} from 'native-base';
import {connect} from 'react-redux';
import { StackActions, NavigationActions } from 'react-navigation';
import styles from './styles';
import {CheckboxOffIcon, CheckboxOnIcon, CheckboxCrossIcon, EyeIcon} from "../../components/icons";
import {validateEmail, validatePassword,validateMobileNumber} from '../../helpers';
import {register, storeCustomerAccessToken} from '../../actions/auth';
import {loadCustomerDetails} from '../../actions/user';
import {setShouldSkip} from '../../actions/general';
import _CountryPicker from '../../components/_CountryPicker';
const digitRegExp = new RegExp('[0-9]');

class Register extends React.Component {
  state = {
    loading: false,
    hidePassword: true,
    email: null,
    password: '',
    firstName: '',
    lastName: '',
    phone: '',
	selectedCountry: {
		"name": "United States",
		"iso2": "us",
		"dialCode": "1",
		"priority": 0,
		"areaCodes": null
	},
  }

  handlePasswordVisibility = () => this.setState({hidePassword: !this.state.hidePassword});
  setValue = (field, value) => this.setState({[field]: value});

  handleRegister = async () => {
    const {email, password, firstName, lastName, phone, selectedCountry} = this.state;

    if(!firstName){
      Alert.alert('Missing Field', 'First Name cannot be empty');
    } else if(!lastName){
      Alert.alert('Missing Field', 'Last name cannot be empty');
    } else if(!phone && phone != "" && !validateMobileNumber(phone)){
      Alert.alert('Invalid Mobile Number', 'Mobile number is invalid')
    } else if(!validateEmail(email)){
      Alert.alert('Invalid Email', 'Please enter a valid email')
    } else if(!validatePassword(password)){
      Alert.alert('Invalid Password', 'Your password should contain at least 6 characters and 1 number');
    }else{
	  this.setState({loading: true});
	  
	  let data = {
		email,
        password,
        firstName : firstName.charAt(0).toUpperCase() + firstName.slice(1),
        lastName : lastName.charAt(0).toUpperCase() + lastName.slice(1),
	  }

	  if(!!phone){
		  data.phone =  "+"+ selectedCountry.dialCode + phone
	  }
      this.props.register(data,(res) =>{
		  if(res == 'error'){
			this.setState({loading: false});
		  }
      });
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
    const {loading, hidePassword, email, password, firstName, lastName, phone} = this.state;
    const {navigation} = this.props;

    return (
		<Container>
			<ImageBackground style={styles.container} source={require('../../assets/images/bg.png')}>
				{/* <SafeAreaView style={styles.innerContainer}>
					<ScrollView> */}
					<TouchableOpacity 
						style={{position:'absolute', top: 40, left: 15, zIndex:1}}
						onPress={() => this.props.navigation.goBack()} 
						>
						<Image 
							source={require('../../assets/icons/left-arrow.png')} 
							resizeMode={'contain'}
							style={{height:20, width: 30}} />
						</TouchableOpacity>
				<Content>
					
					<Image source={require('../../assets/images/logo.png')} style={[styles.logo, {marginBottom: 20}]} />

					<View style={styles.inputFieldsWrap}>
						<Text style={styles.inputFieldLabel}>Please Sign up here:</Text>

						<TextInput
							style={styles.inputField}
							value={firstName}
							placeholder="First Name"
							onChangeText={value => this.setValue('firstName', value)}
						/>

						<TextInput
							style={[styles.inputField,{marginTop:20}]}
							value={lastName}
							placeholder="Last Name"
							onChangeText={value => this.setValue('lastName', value)}
						/>
						<View style={{flexDirection:'row'}}>
							<View style={styles.countryCodeView}>
								<_CountryPicker selectedCountry={this.state.selectedCountry} onValueChange={(val) => this.setState({ selectedCountry: val })} />
							</View>
							
							<TextInput
								style={[styles.mobileInputField,{marginTop:20}]}
								value={phone}
								placeholder="Mobile Number"
								keyboardType={'phone-pad'}
								onChangeText={value => this.setValue('phone', value)}
							/>
						</View>
						

						{/* <TextInput
							style={[styles.inputField,{marginTop:20}]}
							value={email}
							placeholder="Email"
							keyboardType={'phone-pad'}
							onChangeText={value => this.setValue('email', value)}
						/> */}

						<TextInput
							style={[styles.inputField,{marginTop:20}]}
							value={email || ''}
							placeholder="Email"
							keyboardType="email-address"
							textContentType="emailAddress"
							onChangeText={value => this.setValue('email', value)}
							autoCompleteType="email"
							// caretHidden={true}
							autoCapitalize='none'
							autoCorrect={false}
						/>

						{/* {email !== null && (<View style={styles.checkboxWrap}>
						{validateEmail(email) ? <CheckboxOnIcon /> : <CheckboxCrossIcon />}
						<Text style={styles.checkboxText}>{validateEmail(email) ? 'Valid email' : 'Invalid email'}</Text>
						</View>)} */}

						<View style={{marginVertical: 20}}>
						<TextInput
							style={styles.inputField}
							value={password}
							placeholder="Password"
							textContentType="password"
							secureTextEntry={hidePassword}
							blurOnSubmit={false}
							onSubmitEditing={()=> Keyboard.dismiss()}
							onChangeText={value => this.setValue('password', value)}
						/>
						<TouchableOpacity onPress={this.handlePasswordVisibility} style={{position: 'absolute', right: 16, top: 7}}>
							<EyeIcon />
						</TouchableOpacity>
						</View>

						{/* <View onPress={this.handleRememberMe} style={styles.checkboxWrap}>
						{password.length >= 6 ? <CheckboxOnIcon /> : <CheckboxOffIcon />}
						<Text style={styles.checkboxText}>6 characters long</Text>
						</View>

						<View onPress={this.handleRememberMe} style={styles.checkboxWrap}>
						{digitRegExp.test(password) ? <CheckboxOnIcon /> : <CheckboxOffIcon />}
						<Text style={styles.checkboxText}>Contains a number</Text>
						</View> */}
					</View>

					<TouchableOpacity style={[styles.primaryButton, {justifyContent: 'center', flexDirection: 'row', marginTop: 15,  marginHorizontal:50,}]} onPress={this.handleRegister} disabled={loading}>
						{!!loading && <ActivityIndicator />}
						<Text style={[styles.primaryButtonText, {marginLeft: 10}]}>Register</Text>
					</TouchableOpacity>

					{/* <TouchableOpacity onPress={this.handleSkipButton}>
						<Text style={styles.skipButton}>Skip</Text>
					</TouchableOpacity> */}

					{/* <View style={{marginVertical: 8}}>
						<Text style={styles.skipText}>Are you sure you want to skip?</Text>
						<Text style={styles.skipText}>You won't be able to fulfill requests without creating the account.</Text>
					</View>

					<View style={styles.footer}>
						<Text style={styles.footerTitle}>Have an account?</Text>
						<TouchableOpacity onPress={() => navigation.navigate('Login')}>
						<Text style={styles.footerSubtitle}>Sign In here.</Text>
						</TouchableOpacity>
					</View> */}
						{/* </ScrollView>
					</SafeAreaView> */}
					</Content>
				</ImageBackground>
			</Container>
		)
  	}
}

const mapDispatchToProps = dispatch => ({
	setShouldSkip: () => dispatch(setShouldSkip()),
	register: (credentials, callback) => dispatch(register(credentials,callback)),
	loadCustomerDetails: () => dispatch(loadCustomerDetails()),
	storeCustomerAccessToken: token => dispatch(storeCustomerAccessToken(token)),
});

const mapStateToProps = state => ({
  user: state.user,
});

export default connect(mapStateToProps, mapDispatchToProps)(Register);