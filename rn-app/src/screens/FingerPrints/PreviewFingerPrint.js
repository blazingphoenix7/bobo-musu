import React, {Component} from 'react';
import {SafeAreaView, ScrollView, Text, TouchableOpacity, View, Image, Dimensions, Animated} from 'react-native';
import { Container, Content } from 'native-base';
import ImageZoom from 'react-native-image-pan-zoom';
import {connect} from 'react-redux';

import styles from './styles';
import {BackIcon} from '../../components/icons';
import {primaryBackgroundColor} from '../../styles/colors';
import {setTakenFingerPrintPhoto} from '../../actions/fingerprints';
import _Header from '../../components/_Header';
const { height, width } = Dimensions.get('screen');
import { Card } from 'native-base';
import Helptip from './Helptip';

import {
  SoftLightBlend,
  ColorBlend,
  Emboss,
  Earlybird,
  Invert,
  Grayscale,
  RadialGradient,
  Sharpen
} from 'react-native-image-filter-kit';
let isImageUpdate = false
class PreviewFingerPrint extends Component {

  constructor(props){
    super(props);
    this.animatedLeftMargin = new Animated.Value((width - 75) * -1);

    this.state = {
      fpZoomFactor: 1,
      isTutorialOpen: false,
      isAddToCartButton : this.props.navigation.getParam('backToScreen', 'Collections') == "Product"
    }
  }

  componentWillUnmount(){
    if(isImageUpdate){
      isImageUpdate = false
    }
  }
  zoomPreviewIn = () => this.setState({fpZoomFactor: this.state.fpZoomFactor + 0.1});

  usePrint = () => {
    const {takenPhoto} = this.props.fingerprints;

    if(!!takenPhoto){
      const backToScreen = this.props.navigation.getParam('backToScreen', 'Collections');

      this.props.navigation.navigate('SingleFingerPrint', {
        from: backToScreen == "Product" ? 'ConfirmationProduct' : backToScreen,
        hasFingerprintPhoto: true
      });
    }else{
      Alert.alert('Fingerprint Photo Missing', 'Please take a fingerprint');
    }
  }

  retake = () => {
    this.props.setTakenFingerPrintPhoto(null);
    this.props.navigation.goBack();
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
				toValue: (width - 75) * -1,
				duration: 300
			}).start(() =>{
				this.setState({
					isTutorialOpen: status
				})
			})
		}
	}

  render() {
    const { fpZoomFactor, isTutorialOpen, isAddToCartButton } = this.state;
    const {takenPhoto} = this.props.fingerprints;
    const {navigation} = this.props;
    console.log('takenPhoto-->',takenPhoto)
    return (<Container style={styles.container}>
      
      <_Header {...this.props} title={'Name your print'} isMenu={false} />
    

        <Text style={styles.fpPreviewTitle}>{"CONFIRM YOUR FINGERPRINT.\nWE'LL USE THIS PHOTO AS PICTURED"}</Text>

        {/* <Text style={styles.fpPreviewSubtitle}>Your Print:</Text>
        {!!takenPhoto && (<View style={styles.takenPhotoWrap}>
          <ImageZoom
            cropWidth={deviceWidth}
            cropHeight={350}
            imageWidth={350}
            imageHeight={350}
            centerOn={{x: 0, y: 0, scale: fpZoomFactor, duration: 200}}
          >
            
            <Image source={{uri: takenPhoto}} style={[styles.takenPhoto]} resizeMode="contain" />
            
          </ImageZoom>

          <TouchableOpacity onPress={this.zoomPreviewIn} style={styles.zoomInIcon} >
            <Image source={require('../../assets/icons/zoom-in.png')}/>
          </TouchableOpacity>
        </View>)}

        <Text style={[styles.fpPreviewSubtitle, {marginTop: 25}]}>Good Example:</Text>
        <Image source={require('../../assets/images/fingerprint-example.png')} style={styles.takenPhoto} resizeMode="contain" /> */}

        <View style={{flexDirection:'row', marginTop:25}}>
          <View style={{alignItems:'center', justifyContent:'center', flex:1}}>
				<Text style={styles.titleText}>{"YOUR PRINT"}</Text>
				<Card style={{overflow:'hidden', zIndex:0}}>
					{/* <Image source={{uri: takenPhoto}} style={[styles.takenPhoto]} resizeMode="contain" /> */}
          <Sharpen
            image={
              <Image
                style={[styles.takenPhoto]}
                source={{uri: takenPhoto}}
                resizeMode={'contain'}
              />
            }
            onExtractImage={({ nativeEvent }) => {
              if(isImageUpdate == false){
                console.log("takenPhoto-->", takenPhoto) 
                console.log("nativeEvent-->", JSON.stringify(nativeEvent)) 
                this.props.setTakenFingerPrintPhoto(nativeEvent.uri);
                isImageUpdate = true;
              }
              
            }}
            extractImageEnabled={true}
          />
          {/* <Earlybird
            image={
              <ColorBlend
                resizeCanvasTo={'dstImage'}
                dstTransform={{
                  scale: 'CONTAIN'
                }}
                dstImage={
                  <Emboss
                    image={
                      <Image
                        style={[styles.takenPhoto]}
                        source={{uri: takenPhoto}}
                        resizeMode={'contain'}
                      />
                    }
                  />
                }
                srcTransform={{
                  anchor: { x: 0.5, y: 1 },
                  translate: { x: 0.5, y: 1 }
                }}
                srcImage={
                  <Grayscale
                    image={
                      <RadialGradient
                        // colors={['rgba(0, 0, 255, 1)', '#00ff00', 'red']}
                        colors={['#000']}
                        // stops={[0.25, 0.75, 1]}
                        stops={[0.10,0.20,0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1]}
                        center={{ x: '50w', y: '100h' }}
                      />
                    }
                  />
                }
              />
            }
            onExtractImage={({ nativeEvent }) => {
              console.log("nativeEvent-->", JSON.stringify(nativeEvent)) 
              this.props.setTakenFingerPrintPhoto(nativeEvent.uri);
            }}
            extractImageEnabled={true}
          /> */}
				</Card>
		  </View>
		  <View style={{alignItems:'center', justifyContent:'center', flex:1}}>
				<Text style={styles.titleText}>{"GOOD EXAMPLE"}</Text>
				<Card>
					<Image source={require('../../assets/images/fingerprint-example.png')} style={styles.takenPhoto} resizeMode="contain" />
				</Card>
		  </View>
        </View>
        
        <TouchableOpacity style={styles.primaryButton} onPress={this.usePrint}>
          <Text style={styles.buttonText}>Use Print</Text>
        </TouchableOpacity>

        <TouchableOpacity style={[styles.secondaryButton, {marginBottom: 20}]} onPress={this.retake}>
          <Text style={[styles.buttonText, {color: primaryBackgroundColor}]}>Retake your print</Text>
        </TouchableOpacity>

        <TouchableOpacity style={[ styles.secondaryButton, { marginBottom: 20 }]} onPress={() => this.toggleTutorial(true)}>
          <Text style={[ styles.buttonText, { color: primaryBackgroundColor }]}>{"Helpful tips"}</Text>
        </TouchableOpacity>

        {isTutorialOpen && (
					<View style={styles.sidemenuWrap}>
						<Animated.View style={[styles.subSidemenuWrap,{marginLeft: this.animatedLeftMargin}]}>
              <Helptip toggleTutorial={this.toggleTutorial} />
							{/* <View style={styles.sidemenuHeader}>
								<TouchableOpacity onPress={() => this.toggleTutorial(false)} style={{flex:0.2}}>
									<Image source={require('../../assets/icons/left-arrow.png')} resizeMode={'contain'} style={{height: 20, width: 30}} />
								</TouchableOpacity>
								<View style={{flex:1, alignItems:'center', justifyContent:'center'}}>
									<Text style={styles.sidemenuTitle}>{"Helpful tips"}</Text>
								</View>
								<View style={{flex: 0.2}} />
							</View>

							<Content style={{marginTop:10}}>
								<Text style={styles.tutorialSteps}>1. Hold your finger about 5 inches below your phone's camera lens. Make small movements to bring your fingerprint into focus.</Text>
								<Text style={styles.tutorialSteps}>2. Keep steady and tap "Take Photo" </Text>
								<Text style={styles.tutorialSteps}>3. Try using different fingers to get the clearest and most interesting fingerprint</Text>
								<Text style={styles.tutorialSteps}>4. If your print isn't clear, tap "Retake Photo" and try again - it takes a little practice but it's worth the effort!</Text>
								<Text style={styles.tutorialSteps}>5. What you see is what you get - The clearer the print on your screen, the clearer it will appear on your jewelry!</Text>
							</Content> */}

							{/* <Text style={styles.sidemenuNoticeTitle}>The Clearer your photos, the more fingerprint detail you’ll see in your jewerly.</Text>

							<TouchableOpacity style={styles.sidemenuButton} onPress={() => this.toggleTutorial(false)}>
							<Text style={styles.sidemenuButtonText}>Got It</Text>
							</TouchableOpacity> */}
						</Animated.View>
					</View>
				)}
      
    </Container>);
  }
}

const mapDispatchToProps = dispatch => ({
	setTakenFingerPrintPhoto: takenPhoto => dispatch(setTakenFingerPrintPhoto(takenPhoto)),
});

const mapStateToProps = state => ({
  fingerprints: state.fingerprints,
});

export default connect(mapStateToProps, mapDispatchToProps)(PreviewFingerPrint);