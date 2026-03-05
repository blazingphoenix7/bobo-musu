import React, {Component} from 'react';
import {SafeAreaView, ScrollView, Text, TouchableOpacity, View, Image } from 'react-native';
import { Container, Content } from 'native-base';
import {connect} from 'react-redux';
import styles from './styles';

class Helptip extends Component {
  
  render() {
    
    return (
        <View style={{flex:1}}>
            <View style={styles.sidemenuHeader}>
                <TouchableOpacity onPress={() => this.props.toggleTutorial(false)} style={{flex:0.2}}>
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
            </Content>
        </View>
    );
  }
}

const mapDispatchToProps = dispatch => ({

});

const mapStateToProps = state => ({
  
});

export default connect(mapStateToProps, mapDispatchToProps)(Helptip);