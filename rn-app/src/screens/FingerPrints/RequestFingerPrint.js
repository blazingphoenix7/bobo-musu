import React, {Component} from 'react';
import {SafeAreaView, ScrollView, Text, TouchableOpacity, View, TextInput, Alert} from 'react-native';
import {connect} from 'react-redux';

import styles from './styles';
import {BackIcon} from '../../components/icons';
import {sendFingerPrintRequest} from '../../actions/fingerprints';

class RequestFingerPrint extends Component {
  state = {
    recipientEmail: '',
    fingerprintRequested: '',
    messageBody:
`Hi there,

I need your fingerprints for a piece of jewelery. Please download the app and make an account, if you don't have it already, scan your fingerprint, and send it to me.
`,
  }

  sendMessage = () => {
    const {recipientEmail, messageBody} = this.state;

    if(!!recipientEmail && !!messageBody){
      this.props.sendFingerPrintRequest({
        customer_id: 'x',
        from_email: 'x',
        to_email: recipientEmail,
        message: messageBody
      });

      this.props.navigation.navigate('Product');
    }else{
      Alert.alert('Missing Details', 'Please fill all the fields');
    }
  }

  setValue = (field, value) => this.setState({[field]: value});
  goBack = () => this.props.navigation.navigate('Product');

  render() {
    const {recipientEmail, fingerprintRequested, messageBody} = this.state;

    return (<SafeAreaView style={styles.innerContainer}>
      <ScrollView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButtonWrap} onPress={this.goBack}>
            <BackIcon />
          </TouchableOpacity>

          <Text style={styles.title}>Request Fingerprint Photo</Text>
        </View>

        <View style={{marginHorizontal: 20}}>
          <Text style={styles.requestFPNotice}>We'll email to you and your recipeint. Need multiple fingerprints? Send requests individually.</Text>

          <Text style={styles.inputFieldLabel}>To:</Text>
          <TextInput
            style={[styles.inputField, {marginBottom: 20}]}
            value={recipientEmail}
            placeholder="Recipient Email"
            onChangeText={value => this.setValue('recipientEmail', value)}
          />

          <Text style={styles.inputFieldLabel}>Fingerprint Requested:</Text>
          <TextInput
            style={[styles.inputField, {marginBottom: 20}]}
            value={fingerprintRequested}
            placeholder="Whose prints do you need?"
            onChangeText={value => this.setValue('fingerprintRequested', value)}
          />

          <Text style={styles.inputFieldLabel}>Message:</Text>
          <TextInput
            numberOfLines={10}
            multiline={true}
            style={[styles.inputField, {marginBottom: 20}]}
            value={messageBody}
            onChangeText={value => this.setValue('messageBody', value)}
          />
        </View>

        <TouchableOpacity style={styles.primaryButton} onPress={this.sendMessage}>
          <Text style={styles.buttonText}>Send Message</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>);
  }
}

const mapDispatchToProps = dispatch => ({
	sendFingerPrintRequest: params => dispatch(sendFingerPrintRequest(params)),
});

const mapStateToProps = state => ({
  fingerprints: state.fingerprints,
});

export default connect(mapStateToProps, mapDispatchToProps)(RequestFingerPrint);