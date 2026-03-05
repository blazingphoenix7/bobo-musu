import React from 'react';
import {
  SafeAreaView, TextInput, ActivityIndicator,
  View, Text, TouchableOpacity, ScrollView, Alert
} from 'react-native';
import {Container, Content} from 'native-base';
import { connect } from 'react-redux';
import _Header from '../../components/_Header';
import styles from './styles';
import {updateCustomerDetails} from '../../actions/user';
import {EyeIcon} from '../../components/icons';
import { validateMobileNumber, validatePassword } from '../../helpers';
import _CountryPicker from '../../components/_CountryPicker';
import parsePhoneNumber from 'libphonenumber-js'
import { result } from 'lodash';
const countries = require("../../components/_CountryPicker/countries.json");

class MyAccount extends React.Component {
  state = {
    firstName: '',
    lastName: '',
    email: '',
    password: '',
	phone: '',
	hidePassword : true,
	selectedCountry: {
		"name": "United States",
		"iso2": "us",
		"dialCode": "1",
		"priority": 0,
		"areaCodes": null
	},
  }

  setValue = (field, value) => this.setState({[field]: value});

  handleCustomerUpdate = () => {
    const {firstName, lastName, phone, email, password, selectedCountry} = this.state;
    
    if(!firstName && firstName == ''){
      Alert.alert('Missing Field', 'First name cannot be empty');
    } else if(!lastName && lastName == ''){
      Alert.alert('Missing Field', 'Last name cannot be empty');
    } else if(!phone && phone != null && phone != "" && !validateMobileNumber(phone)){
      Alert.alert('Invalid Mobile Number', 'Mobile number is invalid');
    }else{
      const customer = {
        email : email,
		firstName : firstName.charAt(0).toUpperCase() + firstName.slice(1),
        lastName : lastName.charAt(0).toUpperCase() + lastName.slice(1),
      }

      if(!!phone){
          customer.phone = "+" +selectedCountry.dialCode + phone;
      }else{
        customer.phone = null;
      }

      if(!!password){
		if(!validatePassword(password)){
			Alert.alert('Invalid Password', 'Your password should contain at least 6 characters and 1 number');
			return;
		}else{
			customer.password = password;
		}
      }

      this.props.updateCustomerDetails(customer,() =>{
		const {customerDetails} = this.props.user;
		if(customerDetails.phone){
			let phone = parsePhoneNumber(customerDetails.phone);
			if(phone){
				// let selectedCountry = countries.find(x => x.dialCode == phone.countryCallingCode);
				// customerDetails.phone = phone.nationalNumber;
				// customerDetails.selectedCountry = selectedCountry;
				let selectedCountry = countries.filter(x => x.dialCode == phone.countryCallingCode);
			
				customerDetails.phone = phone.nationalNumber;
				if(selectedCountry.length == 1){
					customerDetails.selectedCountry = selectedCountry;
				}else{
					selectedCountry.map(result =>{
						if(result.iso2 == (phone.country && phone.country.toLowerCase())){
							customerDetails.selectedCountry = result;
						}
					})
				}
			}
		}
		this.setState({
		  ...this.state,
		  ...customerDetails
		})
	  });
    }
    // if(!!email){
    //   const customer = {
    //     email
    //   }

    //   if(!!firstName){
    //     customer.firstName = firstName;
    //   }
    //   if(!!lastName){
    //     customer.lastName = lastName;
    //   }
      

    //   this.props.updateCustomerDetails(customer);
    // }else{
    //   Alert.alert('Missing Values', 'Please enter your credentials!')
    // }
  }

  componentDidMount(){
    let {customerDetails} = this.props.user;
	
	if(customerDetails.phone){
		let phone = parsePhoneNumber(customerDetails.phone);
		if(phone){
			let selectedCountry = countries.filter(x => x.dialCode == phone.countryCallingCode);
			
			customerDetails.phone = phone.nationalNumber;
			if(selectedCountry.length == 1){
				customerDetails.selectedCountry = selectedCountry;
			}else{
				selectedCountry.map(result =>{
					if(result.iso2 == (phone.country && phone.country.toLowerCase())){
						customerDetails.selectedCountry = result;
					}
				})
			}
			
		}
	}
    this.setState({
      ...this.state,
      ...customerDetails
    })
  }

  handlePasswordVisibility = () => this.setState({hidePassword: !this.state.hidePassword});

  render(){
    const {firstName, lastName, phone, email, password} = this.state;
    const {updatingCustomerDetails: loading} = this.props.user;

    return (
			<Container>
				<_Header {...this.props} isMenu title={"My Account"} />
				
				<Content>
					<View style={styles.inputFieldsWrap}>
						<Text style={styles.inputFieldLabel}>First Name</Text>
						<TextInput
							style={styles.inputField}
							value={firstName}
							placeholder="First Name"
							onChangeText={value => this.setValue('firstName', value)}
						/>

						<Text style={styles.inputFieldLabel}>Last Name</Text>
						<TextInput
							style={styles.inputField}
							value={lastName}
							placeholder="Last Name"
							onChangeText={value => this.setValue('lastName', value)}
						/>

						<Text style={styles.inputFieldLabel}>Mobile Number</Text>
						{/* <TextInput
							style={styles.inputField}
							value={phone}
							placeholder="Mobile Number (Eg. +16135551111)"
							onChangeText={value => this.setValue('phone', value)}
						/> */}

						<View style={{flexDirection:'row'}}>
							<View style={styles.countryCodeView}>
								<_CountryPicker selectedCountry={this.state.selectedCountry} onValueChange={(val) => this.setState({ selectedCountry: val })} />
							</View>
							
							<TextInput
								style={[styles.mobileInputField]}
								value={phone}
								placeholder="Mobile Number"
								keyboardType={'phone-pad'}
								onChangeText={value => this.setValue('phone', value)}
							/>
						</View>
						

						<Text style={styles.inputFieldLabel}>Email</Text>
						<TextInput
							editable={false}
							style={[styles.inputField,{backgroundColor:'#F3F3F3'}]}
							value={email}
							placeholder="Email"
							keyboardType="email-address"
							textContentType="emailAddress"
							onChangeText={value => this.setValue('email', value)}
							autoCompleteType="email"
							caretHidden={true}
							autoCapitalize='none'
							autoCorrect={false}
						/>

						<Text style={styles.inputFieldLabel}>Password</Text>
						<View>
							<TextInput
								style={styles.inputField}
								value={password}
								placeholder="Change password"
								textContentType="password"
								secureTextEntry={this.state.hidePassword}
								onChangeText={value => this.setValue('password', value)}
							/>
							<TouchableOpacity onPress={this.handlePasswordVisibility} style={{position: 'absolute', right: 16, top: 7}}>
								<EyeIcon />
							</TouchableOpacity>
						</View>
					</View>

					<TouchableOpacity style={[styles.primaryButton, {justifyContent: 'center', flexDirection: 'row', marginTop: 15}]} onPress={this.handleCustomerUpdate} disabled={loading}>
					{!!loading && <ActivityIndicator />}
					<Text style={[styles.primaryButtonText, {marginLeft: 10}]}>Save</Text>
					</TouchableOpacity>
				</Content>
			</Container>
		)
  	}
}

const mapDispatchToProps = dispatch => ({
	updateCustomerDetails: (customer, callback) => dispatch(updateCustomerDetails(customer, callback)),
});

const mapStateToProps = state => ({
  user: state.user,
});

export default connect(mapStateToProps, mapDispatchToProps)(MyAccount);