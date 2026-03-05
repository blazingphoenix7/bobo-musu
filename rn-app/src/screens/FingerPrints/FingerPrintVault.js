import React, {Component} from 'react';
import {SafeAreaView, ScrollView, Text, TouchableOpacity, View, Image } from 'react-native';
import { Container, Content, Icon } from 'native-base';
import {connect} from 'react-redux';
import AsyncStorage from '@react-native-community/async-storage';
import Swipeable from 'react-native-swipeable';
import _Header from '../../components/_Header';
import styles from './styles';
import {MenuIcon} from '../../components/icons';
import {loadFingerPrints, setActiveFingerprintId, deleteFingerPrint} from '../../actions/fingerprints';

class FingerPrintVault extends Component {

  constructor(props){
    super(props);
    this.state = {
      isFromProduct: false
    }
  }

  takeFingerprint = async () => {
    const skipTutorial = await AsyncStorage.getItem('skipTutorial');

    if(!!skipTutorial){
      this.props.navigation.navigate('TakeFingerPrint', {backToScreen: 'FingerPrintVault'});
    }else{
      this.props.navigation.navigate('Tutorial', {backToScreen: 'FingerPrintVault'});
    }
  }

  faqScreen = () => this.props.navigation.navigate('FAQ');
  requestFingerprint = () => this.props.navigation.navigate('RequestFingerPrint');

  openSingleFingerprint = fingerprint => {
    this.props.setActiveFingerprintId(fingerprint.id);
    const navigatingFrom = this.props.navigation.getParam('from', null);
    this.props.navigation.navigate('FingerprintDetail', {
      from: navigatingFrom == "Product" ? "ConfirmationProduct" : 'FingerPrintVault',
      fingerprintName: fingerprint.name,
      fingerprint: fingerprint,
      hasFingerprintPhoto: true
    });
  }

  componentDidMount(){
    const navigatingFrom = this.props.navigation.getParam('from', null);

    if(!!navigatingFrom){
      
      this.setState({
        isFromProduct : navigatingFrom == 'Product' ,
      });
    }
    this.props.loadFingerPrints();
  }

  deleteFingerPrint = (fingerPrint, index) =>{
    this.props.deleteFingerPrint(fingerPrint.id, index);
  }

  render() {
    const {userFingerprints} = this.props.fingerprints;
    const { isFromProduct } = this.state;
    const {customerDetails} = this.props.user;
    return (<Container style={styles.container}>
      <_Header {...this.props} title={'Print Vault'} isMenu={!isFromProduct} />

      <Content>

        <View style={styles.vaultItemsWrap}>
          {userFingerprints.map((fingerprint, index) => {
            const rightButtons = [
              <TouchableOpacity style={{marginTop:13}} onPress={() => this.deleteFingerPrint(fingerprint, index)}>
                <Image source={require('../../assets/icons/delete.png')} style={{height:22, width:22}} resizeMode={'contain'} />
              </TouchableOpacity>,
          ];
          return(
            <Swipeable rightButtons={rightButtons} key={`fingerprints-list-${fingerprint.id}`}>
          <TouchableOpacity style={styles.vaultItem} key={`fingerprints-list-${fingerprint.id}`} onPress={() => this.openSingleFingerprint(fingerprint)}>
            <Text style={styles.vaultItemName}>{fingerprint.fingerprint_title}</Text>
            <Image source={require('../../assets/icons/icon-fingerprint.png')} style={{height:25, width: 20}} resizeMode={'contain'} />
          </TouchableOpacity>
          </Swipeable>
          )})}
        </View>

        <TouchableOpacity style={styles.vaultNotice}>
        {!customerDetails ? <Text style={styles.vaultNoticeText}>Please log in or register to save your prints to the print vault</Text>
          :<Text style={styles.vaultNoticeText}>We store your prints securely.</Text>}
        </TouchableOpacity>

        {!isFromProduct && <TouchableOpacity style={styles.primaryButton} onPress={this.takeFingerprint}>
          <Text style={styles.buttonText}>Take Print Photo</Text>
        </TouchableOpacity>}

        {/* <TouchableOpacity style={[styles.primaryButton, {marginTop: 15}]} onPress={this.requestFingerprint}>
          <Text style={styles.buttonText}>Request Fingerprint</Text>
        </TouchableOpacity> */}
      </Content>
    </Container>);
  }
}

const mapDispatchToProps = dispatch => ({
	loadFingerPrints: () => dispatch(loadFingerPrints()),
	setActiveFingerprintId: fingerprintId => dispatch(setActiveFingerprintId(fingerprintId)),
	deleteFingerPrint: (props, index) => dispatch(deleteFingerPrint(props, index)),
});

const mapStateToProps = state => ({
  fingerprints: state.fingerprints,
  user: state.user
});

export default connect(mapStateToProps, mapDispatchToProps)(FingerPrintVault);