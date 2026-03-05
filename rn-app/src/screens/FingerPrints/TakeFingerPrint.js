import React, {Component} from 'react';
import {SafeAreaView, Text, TouchableOpacity, View, Image, ImageBackground, 
	Alert, ActivityIndicator, Dimensions, Animated, Platform, StyleSheet, TouchableWithoutFeedback} from 'react-native';
import { NavigationEvents } from 'react-navigation';

import {connect} from 'react-redux';
import Jimp from 'jimp';
import {decode, e} from 'base64-arraybuffer';
import {captureException, captureMessage} from '@sentry/react-native';
import ImagePicker from 'react-native-image-crop-picker';
import {primaryBackgroundColor} from '../../styles/colors';
import {setTakenFingerPrintPhoto} from '../../actions/fingerprints';
import {XIcon} from '../../components/icons';
import styles from './styles';

import { RNCamera, FaceDetector } from 'react-native-camera';
import { Container, Content, Icon } from 'native-base';
const { height, width } = Dimensions.get('screen');
import globalVar from '../../constants/globalVar';
import ImagesCombineLibrary from 'react-native-images-combine';
import { filter } from 'lodash';

import Helptip from './Helptip';
const options = {
	width: 800,
	height: 800,
	cropping: true,
	includeBase64: true
};

class TakeFingerPrint extends Component {
	constructor(props){
		super(props);
		
		this.animatedLeftMargin = new Animated.Value((width - 75) * -1)
		this.state = {
			isTutorialOpen: false,
			processing: false,
			focusPoint:{
				x: 0.5,
				y: 0.5,
			},
			autoFocusPoint: {
				normalized: { x: 0.5, y: 0.5 }, // normalized values required for autoFocusPointOfInterest
				drawRectPosition: {
					x: Dimensions.get('window').width * 0.5 - 32,
					y: Dimensions.get('window').height * 0.5 - 32,
				},
			},
		}
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

  	close = () => {
		const backToScreen = this.props.navigation.getParam('backToScreen', 'Collections');
		captureMessage('Closing in TakeFingerPrint ' + backToScreen);
		this.props.navigation.navigate(backToScreen);
	}

	handleTakenImage = response => {
		if(response.didCancel){
			captureMessage('User cancelled image picker');
		}else if(response.error){
			captureMessage('ImagePicker Error: ' + response.error);
		}else if(response.customButton){
			captureMessage('User tapped custom button: ' + response.customButton);
		}else{
			const takenPhoto = response.data;
			captureMessage('Took photo');
			//   console.log('response.data', JSON.stringify(response));
			this.processTakenPhoto(takenPhoto);
		}
	}

	takePicture = async () => {
		if (this.camera) {
			captureMessage('Took photo');
			this.setState({processing: true}, async () =>{
				let options = {}
				if(Platform.OS == 'ios'){
					options = {quality: 1, base64: true, pauseAfterCapture : true,width: 250, orientation: 'landscapeLeft' };
				}else{
					options = {quality: 1, base64: true, pauseAfterCapture : true, width: 250, orientation : 'landscapeLeft' };
				}
				
				const data = await this.camera.takePictureAsync(options);
				// const data = await this.camera.takePictureAsync({orientation : 'auto'});
				
				// console.log('takePicture ', data);
				this.camera.flashMode = false;
				this.processTakenPhoto(data.base64);
			});
		}
	};

	processTakenPhoto = async (takenPhoto) => {

		const imageBuffer = decode(takenPhoto);
		
		captureMessage('buffer decoded');

		const buffers = [imageBuffer, imageBuffer].map(image => Jimp.read(image));
		console.log('buffers',buffers.length);

		// var loadFont = await Jimp.loadFont("../../assets/fonts/open-sans-16-black.fnt");
		Promise
			.all(buffers)
			.then(jimps => {
				// Jimp.loadFont(Jimp.FONT_SANS_64_BLACK).then(font => {
					const first = jimps[0]
						// .resize(240,240)
						.quality(100)
						.greyscale()
						.invert()
						.contrast(1)
						// .contrast(-1)
						// .brightness(0)
						// .autocrop(2)
						.blur(5);

					captureMessage('promise 1 passed');

				jimps[1]
					.quality(100)
					.brightness(.5)
					.invert()
					.greyscale()
					// .contrast(.3)
					// .autocrop(2)
					// .greyscale()
					// .dither565()
					.composite(first, 0, 0, {
						mode: Jimp.BLEND_ADD
					})
					// .scale(20)
					.convolute([[-2, -1, 0], [-1, 1, 1], [0, 1, 2]])
					// .convolute([[-2, -1, 0], [-1, 1, 1], [0, 1, 2]])
					// .convolute([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
					// .convolute([[0, 0, 0], [-1, 1, 0], [0, 0, 0]])
					// .convolute([[2,1,0], [1,1,-1], [0,-1,-2]])
					// .resize(240,240)
					// .print(Jimp.FONT_SANS_10_BLACK,0,0,{
					// 	text: 'Hello world!',
					// 	alignmentX: Jimp.HORIZONTAL_ALIGN_CENTER,
					// 	alignmentY: Jimp.VERTICAL_ALIGN_MIDDLE
					// })
					// .sepia()
					.rotate(Platform.OS == 'ios' ? 90 : -90)
					// .autocrop(10)
					.getBase64(Jimp.MIME_JPEG, (err, results) => {
						// this.setState({processing: false});
						captureMessage('base64 done');
						// console.log('results-->',results)
						this.setState({processing: false});
						if(err){
							console.log('Error while reading the photo', err);
							captureException(err);
						}else{
							captureMessage('photo taken processed ' + !!results);
							this.props.setTakenFingerPrintPhoto(results);
							const backToScreen = this.props.navigation.getParam('backToScreen', 'Collections');
							this.props.navigation.navigate('PreviewFingerPrint', {backToScreen});
						}
					});
				// });
			})
			.catch(err => {
				this.setState({processing: false});

				console.log("Error image",err);
				this.camera.resumePreview();
				this.camera.flashMode = false
				captureException(err);
				Alert.alert('Could not process the image');
			});
		
	}

	touchToFocus(event) {
		const { pageX, pageY } = event.nativeEvent;
		const screenWidth = Dimensions.get('window').width;
		const screenHeight = Dimensions.get('window').height;
		const isPortrait = screenHeight > screenWidth;
	
		let x = pageX / screenWidth;
		let y = pageY / screenHeight;
		// Coordinate transform for portrait. See autoFocusPointOfInterest in docs for more info
		if (isPortrait) {
			x = pageY / screenHeight;
			y = -(pageX / screenWidth) + 1;
		}
		console.log('pageX-->', x)
		console.log('pageY-->', y)
		this.setState({
			// autoFocus : { x: x, y: y }
		  autoFocusPoint: {
			normalized: { x, y },
			drawRectPosition: { x: pageX, y: pageY },
		  },
		});
	}

	render() {
    	const {isTutorialOpen, processing} = this.state;
		const drawFocusRingPosition = {
			top: this.state.focusPoint.y,
			left: this.state.focusPoint.x - 32,
		};
		const backToScreen = this.props.navigation.getParam('backToScreen', 'Collections');
		return (
				<SafeAreaView style={styles.innerContainer}>
					<NavigationEvents
						onWillFocus={payload => console.log('will focus', payload)}
						onDidFocus={payload => this.camera && this.camera.resumePreview(0)}
						onWillBlur={payload => console.log('will blur', payload)}
						onDidBlur={payload => console.log('did blur', payload)}
						/>
					<TouchableOpacity 
							style={{position:'absolute', top: 40, right: 15, zIndex:1}}
							onPress={() => this.props.navigation.navigate(backToScreen)} 
						>
							<Icon type={'Entypo'} name={'cross'} style={{fontSize: 30}} />
					</TouchableOpacity>

					<View style={{
							height: 155, 
							// height: height, 
							width: width - 110,
							// width: width,
							// backgroundColor:'red',
									marginHorizontal:20,
										zIndex:0,
										top: globalVar.isIphoneX ? height * .32 : height * .28,
										position:'absolute'}} 
						onLayout={event => {
									const layout = event.nativeEvent.layout;
									console.log('height:', layout.height);
									console.log('width:', layout.width);
									console.log('x:', layout.x);
									console.log('y:', layout.y);

									this.setState({
										focusPoint : {
											x : (width / 2),
											y: (layout.y) - 32 
										}
									})

  								}}>
								<RNCamera
									ref={ref => {
										this.camera = ref;
									}}
									style={{
										flex:1
									}}
									type={'back'}
									// flashMode={Platform.OS == 'ios'? 'on' : 'torch'}
									flashMode={Platform.OS == 'ios'? 'on' : 'on'}
									// flashMode={'torch'}
									autoFocus={'on'}
									// autoFocusPointOfInterest={this.state.focusPoint}
									// autoFocusPointOfInterest={this.state.autoFocusPoint.normalized}
									zoom={Platform.OS == 'ios' ? 0.012 : 0.2}
									maxZoom={0.5}
									whiteBalance={'auto'}
									// showViewFinder={false}
									focusDepth={0}
									ratio={"1:1"}
									useNativeZoom
									androidCameraPermissionOptions={{
										title: 'Permission to use camera',
										message: 'We need your permission to use your camera',
										buttonPositive: 'Ok',
										buttonNegative: 'Cancel',
									}}
								/>
							</View>
				
					<ImageBackground style={[styles.container]} source={require('../../assets/images/take_fingerprint.png')} >
						{processing && (<View style={styles.activityIndicatorWrap}>
							<ActivityIndicator size="large" color="white" />
						</View>)}
						<View style={{flex:1, justifyContent:'space-between', backgroundColor:'transparent'}}>
							<View style={{backgroundColor:'transparent', marginTop: (Platform.OS == "android") ? 45 : 25}}>
								<Text style={styles.heading}>{"Hold your finger under your device's camera until your finger is positioned within the dotted lines and your prints are in focus"}</Text>
							</View>
							
							<View style={{backgroundColor:'transparent'}}>
								<View style={{}}>
									<Text style={styles.heading}>{"When your print is in focus, tap the camera button."}</Text>
								</View>

								<TouchableOpacity style={[ styles.secondaryButton, { marginBottom: 20 }]} onPress={() => this.toggleTutorial(true)}>
									<Text style={[ styles.buttonText, { color: primaryBackgroundColor }]}>{"Helpful tips"}</Text>
								</TouchableOpacity>

								<TouchableOpacity onPress={this.takePicture} style={styles.captureButton}>
									<Image source={require('../../assets/icons/capture.png')} style={styles.captureButtonImage} />
								</TouchableOpacity>
							</View>
						</View>
					</ImageBackground>
				
				{isTutorialOpen && (
					<View style={styles.sidemenuWrap}>
						<Animated.View style={[styles.subSidemenuWrap,{marginLeft: this.animatedLeftMargin}]}>
							<Helptip toggleTutorial={this.toggleTutorial} />
						</Animated.View>
					</View>
				)}
			</SafeAreaView>
		)
  	}
}


const mapDispatchToProps = dispatch => ({
	setTakenFingerPrintPhoto: takenPhoto => dispatch(setTakenFingerPrintPhoto(takenPhoto)),
});

export default connect(null, mapDispatchToProps)(TakeFingerPrint);

