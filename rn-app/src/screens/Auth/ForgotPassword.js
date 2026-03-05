import React from 'react';
import {SafeAreaView, TextInput, Image, View, Text, TouchableOpacity, Alert, ActivityIndicator} from 'react-native';
import { Container, Content } from 'native-base';
import {connect} from 'react-redux';

import _Header from '../../components/_Header';
import styles from './styles';
import {CheckboxOnIcon, CheckboxCrossIcon, BackArrowIcon} from "../../components/icons";
import {validateEmail} from '../../helpers';
import {forgotPassword, resetForgotPasswordStatus} from '../../actions/auth';

class ForgotPassword extends React.Component {
  state = {
    loading: false,
    email: null,
  }

  setValue = (field, value) => this.setState({[field]: value});

  handleResetPassword = () => {
    const {email} = this.state;

    if(validateEmail(email)){
      this.setState({loading: true});
      this.props.forgotPassword(email);
    }else{
      Alert.alert('Incorrect Email', 'Please enter your email!')
    }
  }

  componentDidUpdate(){
    const {forgotPasswordStatus} = this.props.user;

    if(this.state.loading && forgotPasswordStatus !== null){
      this.setState({loading: false});

      if(forgotPasswordStatus === true){
        Alert.alert('Success', 'Please check your email to complete resetting your password', [
          {
            text: 'Got it',
            style: 'default',
            onPress: () => {
              this.props.resetForgotPasswordStatus();
              this.props.navigation.goBack();
            }
          }
        ]);
      }else{
        Alert.alert('Error', forgotPasswordStatus, [
          {
            text: 'Try again',
            style: 'default',
            onPress: () => {
              this.props.resetForgotPasswordStatus();
            }
          }
        ]);
      }
    }
  }

  render(){
    const {loading, email} = this.state;
    const {navigation} = this.props;

    return (
		
			<Container>
        <_Header {...this.props} title={'Reset Password'} />
				<Content>
					<Image source={require('../../assets/images/logo-row.png')} style={styles.logo} />

					<Text style={styles.notice}>Please input your Email here and we will send you link to reset the password.</Text>

					<View style={styles.inputFieldsWrap}>
						<TextInput
						style={styles.inputField}
						value={email}
						placeholder="Email"
						keyboardType="email-address"
						textContentType="emailAddress"
						onChangeText={value => this.setValue('email', value)}
						autoCompleteType="email"
						/>

						{/* {email !== null && (<View onPress={this.handleRememberMe} style={styles.checkboxWrap}>
						{validateEmail(email) ? <CheckboxOnIcon /> : <CheckboxCrossIcon />}
						<Text style={styles.checkboxText}>{validateEmail(email) ? 'Valid email' : 'Invalid email'}</Text>
						</View>)} */}
					</View>

					<TouchableOpacity style={[styles.primaryButton, {marginTop: 40, justifyContent: 'center', flexDirection: 'row', marginHorizontal:50}]} onPress={this.handleResetPassword} disabled={loading}>
						{!!loading && <ActivityIndicator />}
						<Text style={[styles.primaryButtonText, {marginLeft: 10}]}>Next</Text>
					</TouchableOpacity>
				</Content>
			
			</Container>
		)
	}
}

const mapDispatchToProps = dispatch => ({
	forgotPassword: credentials => dispatch(forgotPassword(credentials)),
	resetForgotPasswordStatus: () => dispatch(resetForgotPasswordStatus()),
});

const mapStateToProps = state => ({
  user: state.user,
});

export default connect(mapStateToProps, mapDispatchToProps)(ForgotPassword);