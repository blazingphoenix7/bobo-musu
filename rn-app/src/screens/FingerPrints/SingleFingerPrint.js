import React, {Component} from 'react';
import {SafeAreaView, Text, TouchableOpacity, View, 
  Image, Dimensions, TextInput, Alert, ActivityIndicator } from 'react-native';

import { Container, Content } from 'native-base';
import ImageZoom from 'react-native-image-pan-zoom';
import {connect} from 'react-redux';
import {KeyboardAwareScrollView} from 'react-native-keyboard-aware-scrollview'

import styles from './styles';
import {BackIcon} from '../../components/icons';
import {primaryBackgroundColor} from '../../styles/colors';
import {setTakenFingerPrintPhoto, addNewFingerPrint} from '../../actions/fingerprints';
import {setProductAssignPrint} from '../../actions/products';
import _Header from '../../components/_Header';
const {width: deviceWidth} = Dimensions.get('window');

class SingleFingerPrint extends Component {
  constructor(props){
    super(props);
    const { tempFingerPrintData } = props.fingerprints;
    this.state = {
      navigatingFrom: null,
      fingerprintName: '',
      hasFingerprintPhoto: false,
      fpZoomFactor: 1,
      loading: false
    }
    if(tempFingerPrintData != undefined){
      console.log('tempFingerPrintData',tempFingerPrintData);
      props.setTempFingerPrintData(undefined)
    }
  }
  

  retake = () => {
    this.props.setTakenFingerPrintPhoto(null);
    this.props.navigation.navigate(this.state.navigatingFrom);
  }

  usePrint = () => {
    const {fingerprintName, hasFingerprintPhoto} = this.state;

    if(!!fingerprintName && hasFingerprintPhoto){
      const fingerprintPhoto = this.props.fingerprints.takenPhoto;
      const {customerDetails} = this.props.user;

      if (!!customerDetails && customerDetails.id) {
        const {userFingerprints} = this.props.fingerprints;
        let isExistName = userFingerprints.find(x => x.fingerprint_title.toUpperCase() == fingerprintName.toUpperCase())
        console.log('isExistName-->',isExistName)
        if(isExistName == undefined){
          this.setState({
            loading : true
          })
          this.props.addNewFingerPrint(fingerprintName, fingerprintPhoto,(e) => {
            
            if(this.state.navigatingFrom == "ConfirmationProduct"){
              this.props.setProductAssignPrint(e);
            }
            
            this.setState({
              loading : false
            },() =>{
              if(e){
                this.props.navigation.navigate(this.state.navigatingFrom);
              }
            });
            
          });  
        } else {
          Alert.alert('Fingerprint Name Duplicate', 'Please give your fingerprint a unique name.');
        }
        
      }else{
        const backToScreen = this.props.navigation.getParam('backToScreen', 'Collections')
        Alert.alert(
          'Registration Required',
          'To continue, you need to login or create a new account',
          [
            {
              text: 'Login',
              style: 'default',
              onPress: () => {
                this.props.setTempFingerPrintData({
                  fingerprintPhoto : fingerprintPhoto,
                  fingerprintName : fingerprintName,
                  backToScreen : this.state.navigatingFrom
                })
                this.props.navigation.navigate('Auth', {backToScreen: 'SingleFingerPrint'})
              }
            },
            {
              text: 'Cancel',
              style: 'cancel'
            },
          ]
        ); 
      }
    }else{
      Alert.alert('Fingerprint Name Missing', 'Please give your fingerprint a unique name.');
    }
  }

  setValue = (field, value) => this.setState({[field]: value});

  componentDidMount(){
    const navigatingFrom = this.props.navigation.getParam('from', null);

    if(!!navigatingFrom){
      const fingerprintName = this.props.navigation.getParam('fingerprintName', '');
      const hasFingerprintPhoto = this.props.navigation.getParam('hasFingerprintPhoto', false);

      this.setState({
        navigatingFrom,
        hasFingerprintPhoto,
        fingerprintName
      });
    }
  }

  render() {
    const {fingerprintName, fpZoomFactor,loading} = this.state;
    const {takenPhoto: fingerprintPhoto} = this.props.fingerprints;
    const navigation = this.props.navigation;

    return (<Container style={styles.container}>
       <_Header {...this.props} title={'Name your print'} isMenu={false} />

      {loading && (<View style={[styles.activityIndicatorWrap,{top:0}]}>
        <ActivityIndicator size="large" color="white" />
      </View>)}
      <KeyboardAwareScrollView
        style={[styles.container, {width: '100%'}]}
        scrollEnabled={true}
        enableAutomaticScroll={true}
      >
        {/* <View style={styles.header}>
          <TouchableOpacity style={styles.backButtonWrap} onPress={() => navigation.goBack()}>
            <BackIcon />
          </TouchableOpacity>

          <Text style={styles.title}>Name your print</Text>
          <View style={{height: 16, width: 18}} />
        </View> */}

        {/* <Text style={styles.fpPreviewSubtitle}>Your Print:</Text> */}
        {!!fingerprintPhoto && (<View style={{width: deviceWidth, alignItems:'center'}}>
          {/* <ImageZoom
            cropWidth={deviceWidth}
            cropHeight={350}
            imageWidth={350}
            imageHeight={350}
            centerOn={{x: 0, y: 0, scale: fpZoomFactor, duration: 200}}
          > */}
            <Image source={{uri: fingerprintPhoto}} style={styles.previewTakenPhoto} resizeMode="contain" />
          {/* </ImageZoom> */}

          {/* <TouchableOpacity onPress={this.zoomPreviewIn} style={styles.zoomInIcon} >
            <Image source={require('../../assets/icons/zoom-in.png')}/>
          </TouchableOpacity> */}
        </View>)}

        <View style={styles.inputFieldsWrap}>
          <Text style={styles.inputFieldLabel}>Print Name</Text>
          <TextInput
            style={styles.inputField}
            maxLength={30}
            value={fingerprintName}
            placeholder="Name"
            onChangeText={value => this.setValue('fingerprintName', value)}
          />
        </View>

        <TouchableOpacity style={styles.primaryButton} onPress={this.usePrint}>
          <Text style={styles.buttonText}>Use this print</Text>
        </TouchableOpacity>

        {/* <TouchableOpacity style={[styles.secondaryButton, {marginBottom: 20}]} onPress={this.retake}>
          <Text style={[styles.buttonText, {color: primaryBackgroundColor}]}>Retake this photo</Text>
        </TouchableOpacity> */}
      </KeyboardAwareScrollView>
    </Container>);
  }
}

const mapDispatchToProps = dispatch => ({
  setTakenFingerPrintPhoto: fingerprintPhoto => dispatch(setTakenFingerPrintPhoto(fingerprintPhoto)),
  addNewFingerPrint: (fingerprintName, fingerprintPhoto, callback) => dispatch(addNewFingerPrint(fingerprintName, fingerprintPhoto, callback)),
  setProductAssignPrint: (props) => dispatch(setProductAssignPrint(props)),
  setTempFingerPrintData : (props) => dispatch({
    type: 'SET_TEMP_FINGER_PRINT_DATA',
    payload: props
})
});

const mapStateToProps = state => ({
  user: state.user,
  fingerprints: state.fingerprints,
});

export default connect(mapStateToProps, mapDispatchToProps)(SingleFingerPrint);