import React, {Component} from 'react';
import {SafeAreaView, Text, TouchableOpacity, View, 
  Image, Dimensions, TextInput, Alert, ActivityIndicator, Animated } from 'react-native';

import { Container, Content, Icon } from 'native-base';
import ImageZoom from 'react-native-image-pan-zoom';
import {connect} from 'react-redux';
import {KeyboardAwareScrollView} from 'react-native-keyboard-aware-scrollview'

import styles from './styles';
import {BackIcon} from '../../components/icons';
import {primaryBackgroundColor} from '../../styles/colors';
import {setTakenFingerPrintPhoto, addNewFingerPrint} from '../../actions/fingerprints';
import { setProductAssignPrint } from '../../actions/products';
import _Header from '../../components/_Header';
import Helptip from './Helptip';
const {width: deviceWidth} = Dimensions.get('window');

class FingerprintDetail extends Component {

  constructor(props){
    super(props);

    this.animatedLeftMargin = new Animated.Value((deviceWidth - 75) * -1);

    this.state = {
      navigatingFrom: props.navigation.getParam('from', null),
      fingerprintName: '',
      hasFingerprintPhoto: false,
      fpZoomFactor: 1,
      loading: false,
      fingerprint : this.props.navigation.getParam('fingerprint', null),
      isTutorialOpen: false,
    }
  }
  


    usePrint = () => {
      this.props.setProductAssignPrint(this.state.fingerprint);
      this.props.navigation.navigate(this.state.navigatingFrom);
    }

    componentDidMount(){
     
    }

    toggleTutorial = status => {
      if(status){
        this.setState({
          isTutorialOpen: status
        },()=>{
          Animated.timing(this.animatedLeftMargin, {
            toValue: 0,
            duration: 300
          }).start()
          
        });
      }else{	
        Animated.timing(this.animatedLeftMargin, {
          toValue: (deviceWidth - 75) * -1,
          duration: 300
        }).start(() =>{
          this.setState({
            isTutorialOpen: status
          })
        })
      }
    }

    render() {
        const {fingerprintName, fpZoomFactor,loading, isTutorialOpen, navigatingFrom} = this.state;
        const {takenPhoto: fingerprintPhoto} = this.props.fingerprints;
        const navigation = this.props.navigation;

        return (
            <Container style={styles.container}>
                <_Header {...this.props} title={'Fingerprint vault'} isMenu={false} />

                {loading && (<View style={[styles.activityIndicatorWrap,{top:0}]}>
                    <ActivityIndicator size="large" color="white" />
                </View>)}
                <KeyboardAwareScrollView
                    style={[styles.container, {width: '100%'}]}
                    scrollEnabled={true}
                    enableAutomaticScroll={true}
                >
                    
                    <Text style={styles.fpPreviewSubtitle}>{"Confirm your\nfingerprint. We'll use\nthis photo as pictured"}</Text>

                    <TouchableOpacity style={{alignSelf:'flex-start', marginLeft:20, flexDirection:'row', alignItems:'center', justifyContent:'center'}} onPress={() => this.toggleTutorial(true)}>
                      
                      <Text style={[styles.buttonText, {color: primaryBackgroundColor, textDecorationLine:'underline'}]}>{"Helpful tips "}
                      <Icon type={'AntDesign'} name={'caretdown'} style={{fontSize:12, color: primaryBackgroundColor}} />
                      </Text>
                    </TouchableOpacity>
                    <View style={{width: deviceWidth, alignItems:'center'}}>
                        <Image source={{uri: this.state.fingerprint.fingerprint_file}} style={styles.previewTakenPhoto} resizeMode="contain" />
                    </View>

                   
                    {(navigatingFrom != "FingerPrintVault") && <TouchableOpacity style={styles.primaryButton} onPress={this.usePrint}>
                      <Text style={styles.buttonText}>Use this print</Text>
                    </TouchableOpacity>}

                    
            </KeyboardAwareScrollView>

            {isTutorialOpen && (
					<View style={styles.sidemenuWrap}>
						<Animated.View style={[styles.subSidemenuWrap,{marginLeft: this.animatedLeftMargin}]}>
              <Helptip toggleTutorial={this.toggleTutorial} />
						</Animated.View>
					</View>)}
        </Container>);
    }
}

const mapDispatchToProps = dispatch => ({
  setTakenFingerPrintPhoto: fingerprintPhoto => dispatch(setTakenFingerPrintPhoto(fingerprintPhoto)),
  addNewFingerPrint: (fingerprintName, fingerprintPhoto, callback) => dispatch(addNewFingerPrint(fingerprintName, fingerprintPhoto, callback)),
  setProductAssignPrint: (props) => dispatch(setProductAssignPrint(props)),
});

const mapStateToProps = state => ({
  user: state.user,
  fingerprints: state.fingerprints,
});

export default connect(mapStateToProps, mapDispatchToProps)(FingerprintDetail);