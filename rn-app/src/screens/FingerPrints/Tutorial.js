import React, {Component} from 'react';
import {SafeAreaView, ScrollView, View, Text, TouchableOpacity, Image, Dimensions} from 'react-native';
import { Container, Content } from 'native-base';
import {connect} from 'react-redux';
import {SliderBox} from "react-native-image-slider-box";
import AsyncStorage from '@react-native-community/async-storage';

import styles from './styles';
import {BackArrowIcon} from '../../components/icons';
import {primaryBackgroundColor} from '../../styles/colors';
import _Header from '../../components/_Header';
const { height, width } = Dimensions.get("window");

const tutorialImages = [
  require('../../assets/images/tutorial-step-01.png'),
  require('../../assets/images/tutorial-step-02.png'),
  require('../../assets/images/tutorial-step-03.png')
];

const slidesTexts = [
  'First, place the finger 25 cm away from the lens.',
  'Align the finger as pictured, so that the tip is under the dotted oval.',
  'Take the photo. Don’t worry, you can always retake it!'
];

class Tutorial extends Component {
  state = {
    currentSlide: 0
  }

  onCurrentSlide = index => this.setState({ currentSlide: index });

  close = () => {
    const backToScreen = this.props.navigation.getParam('backToScreen', 'Collections');
    this.props.navigation.navigate(backToScreen);
  }

  proceed = () => {
    const backToScreen = this.props.navigation.getParam('backToScreen', 'Collections');
    this.props.navigation.navigate('TakeFingerPrint', {backToScreen});
    // this.props.navigation.navigate('TakeFingerPrint');
  }

  skipTutorial = async () => {
    await AsyncStorage.setItem('skipTutorial', 'true');
    this.proceed();
  };
  
  render(){
    const {currentSlide} = this.state;

    return (<Container style={styles.container}>

      <_Header {...this.props} title={'Add Fingerprint Photo'} isMenu={false} onPress={() => this.props.navigation.goBack()} />
      {/* <ScrollView style={styles.container}> */}

        {/* <View style={styles.header}>
          <TouchableOpacity onPress={this.close}>
            <BackArrowIcon />
          </TouchableOpacity>

          <Text style={styles.title}></Text>
        </View> */}

        {/* <SliderBox
          images={tutorialImages}
          style={styles.tutorialAnimationImages}
          sliderBoxHeight={350}
          disableOnPress={false}
          currentImageEmitter={this.onCurrentSlide}
          autoplay
          dotColor="#CF9B2D"
          inactiveDotColor="transparent"
          dotStyle={{
            borderColor: '#D09B2C',
            borderWidth: 1,
            width: 15,
            height: 15,
            borderRadius: 15,
            padding: 0,
            margin: 0
          }}
          paginationBoxStyle={{
            position: "absolute",
            bottom: 0
          }}
        /> */}
        <View style={{flex:1, alignItems:'center', justifyContent:'center'}}>
          <Image source={require('../../assets/images/tutorial.gif')} style={{height : height * .4, width: width - 100, alignSelf: 'center'}} />
        </View>

        <View>
          <Text style={styles.tutorialAnimationText}>{"On the next step, place your\nfingertip as shown on this\ntutorial and take a photo"}</Text>

          <TouchableOpacity style={styles.primaryButton} onPress={this.proceed}>
            <Text style={styles.buttonText}>Got it</Text>
          </TouchableOpacity>

          <TouchableOpacity style={[styles.secondaryButton, {marginBottom: 20, borderWidth: 0}]} onPress={this.skipTutorial}>
            <Text style={[styles.buttonText, {color: primaryBackgroundColor, textDecorationLine:'underline'}]}>Don’t show this again</Text>
          </TouchableOpacity>
        </View>

      {/* </ScrollView> */}
    </Container>)
  }
}

const mapStateToProps = state => ({
  fingerprints: state.fingerprints
})

const mapDispatchToProps = dispatch => ({
	setTakenFingerPrintPhoto: takenPhoto => dispatch(setTakenFingerPrintPhoto(takenPhoto)),
});

export default connect(mapStateToProps, mapDispatchToProps)(Tutorial);
