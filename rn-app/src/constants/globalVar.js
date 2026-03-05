import { Dimensions, Platform } from 'react-native';

const { height, width } = Dimensions.get('window');
const globalVar = {
    isIphoneX : Platform.OS === 'ios' && (height > 800 || width > 800) ? true : false
}

export default globalVar