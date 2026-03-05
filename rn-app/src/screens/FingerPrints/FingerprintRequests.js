import React, {Component} from 'react';
import {SafeAreaView, ScrollView, Text, TouchableOpacity, View} from 'react-native';
import {connect} from 'react-redux';
import AsyncStorage from '@react-native-community/async-storage';

import styles from './styles';
import {MenuIcon} from '../../components/icons';
import {loadFingerPrintRequests} from '../../actions/fingerprints';

class FingerPrintRequests extends Component {

  takeFingerprint = async () => {
    const skipTutorial = await AsyncStorage.getItem('skipTutorial');

    if(!!skipTutorial){
      this.props.navigation.navigate('TakeFingerPrint', {backToScreen: 'FingerPrintRequests'});
    }else{
      this.props.navigation.navigate('Tutorial', {backToScreen: 'FingerPrintRequests'});
    }
  }

  componentDidMount(){
    const {customerDetails} = this.props.user;

    if(!!customerDetails && customerDetails.id){
      this.props.loadFingerPrintRequests(customerDetails.id);
    }
  }

  render() {
    const {fingerprintRequests} = this.props.fingerprints;
    console.log(fingerprintRequests)

    return (<SafeAreaView style={styles.innerContainer}>
      <ScrollView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => this.props.navigation.openDrawer()}>
            <MenuIcon />
          </TouchableOpacity>

          <Text style={styles.title}>Fingerprint Requests</Text>
        </View>

        <View style={styles.vaultItemsWrap}>
          {fingerprintRequests.map((fingerprint, index) => (<TouchableOpacity style={styles.vaultItem} key={`fingerprints-list-${index}`} onPress={() => this.openSingleFingerprint(fingerprint)}>
            <Text style={styles.vaultItemName}>{fingerprint.name}</Text>
          </TouchableOpacity>))}
        </View>

        <TouchableOpacity style={styles.vaultNotice}>
          <Text>We store your prints securely.</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.primaryButton} onPress={this.takeFingerprint}>
          <Text style={styles.buttonText}>Take Print Photo</Text>
        </TouchableOpacity>

        <TouchableOpacity style={[styles.primaryButton, {marginTop: 15}]} onPress={this.requestFingerprint}>
          <Text style={styles.buttonText}>Request Fingerprint</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>);
  }
}

const mapDispatchToProps = dispatch => ({
	loadFingerPrintRequests: customerId => dispatch(loadFingerPrintRequests(customerId)),
});

const mapStateToProps = state => ({
  user: state.user,
  fingerprints: state.fingerprints,
});

export default connect(mapStateToProps, mapDispatchToProps)(FingerPrintRequests);