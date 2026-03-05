import React, {Component} from 'react';
import {
  SafeAreaView, Image, ScrollView, View, Text,
  TouchableOpacity, TouchableWithoutFeedback,
  ActivityIndicator, Modal, Alert, Dimensions
} from 'react-native';
import {Picker} from '@react-native-community/picker';
import {SliderBox} from "react-native-image-slider-box";
import {connect} from 'react-redux';
import _Header from '../../components/_Header';
import styles from './styles';
import * as Colors from '../../styles/colors';
import {BackArrowIcon, HeartSolidIcon, HeartHollowIcon} from "../../components/icons";
import { getOrderFulfillmentData } from '../../actions/orders'
import { Container, Content } from 'native-base';
import moment from 'moment';
import _ from 'lodash';
let filteringOptions = {};
const {height: deviceHeight, width: deviceWidth} = Dimensions.get('window');

class ProductDetails extends Component {
  constructor(props) {
    super(props);
    this.state = {
      productDetail : props.navigation.getParam('productId', null),
      isLoading: false
    };
  }


    componentDidMount() {
        console.log('productDetail-->', JSON.stringify(this.state.productDetail));
        // if(this.state.productDetail.fulfillmentStatus == "FULFILLED"){
            if(this.state.productDetail){
                let id = this.state.productDetail.id
                let fulfillmentsId = _.get(this.state.productDetail,'orderData.fulfillments[0].id') || undefined
                if(fulfillmentsId){
                    this.setState({
                        isLoading: true
                    });
                    this.props.getOrderFulfillmentData(id,fulfillmentsId,() =>{
                        this.setState({
                            isLoading: false
                        }); 
                    });
                }
            }
            
        // }
    }

    render() {
        const {
            productDetail,isLoading
        } = this.state;
        const { fulfillmentData } = this.props.orders;
        const {navigation, products, fingerprints} = this.props;
        const product = productDetail;
        let productAttributes = {};

        let expectedDeliveryDate = '';
        if(fulfillmentData){
            expectedDeliveryDate = moment(fulfillmentData.estimated_delivery_at).format("DD/MM/YYYY") 
        }else{
            if(productDetail){
                let date = new Date(productDetail?.orderData?.created_at);
                expectedDeliveryDate = moment(date.setDate(date.getDate() + 28)).format("DD/MM/YYYY");
            }
        }
        
        return !!product ? (
        <Container>
            <_Header {...this.props} title={product.title} />
            <Content>
            <View style={styles.singleProductImages}>
                <SliderBox
                inactiveDotColor={'#D3D3D3'}
                dotColor={'#808080'}
                disableOnPress={true}
                images={[product.image]}
                style={styles.singleProductImage}
                imageLoadingColor={'#D3D3D3'}
                resizeMode={'contain'}
                paginationBoxStyle={{
                    position: 'absolute',
                    bottom: -10,
                    padding: 0,
                    alignItems: 'center',
                    alignSelf: 'center',
                    justifyContent: 'center',
                    paddingVertical: 10,
                }}
                />
            </View>

            {/* <Text style={styles.singleProductTitle}>{product.title}</Text>
                        <Text style={styles.singleProductPrice}>${price && Number(price).toFixed(2) || Number(product.priceRange.minVariantPrice.amount).toFixed(2)}</Text>
                        {!!product.description && <Text style={styles.singleProductDescription} numberOfLines={3} ellipsizeMode="tail">{product.description}</Text>}

                        <View style={styles.singleProductVariants}>
                            {this.renderFilteringDropdowns()}
                        </View> */}

            <View>
                <Text style={styles.singleProductTitle}>{product.title}</Text>
                <Text style={styles.singleProductDescription}>{`Finger print name: ${product.fingerprintName}`}</Text>
                <Text style={styles.singleProductPrice}>${product.price}</Text>
            </View>
            
            <View style={{marginTop: 10}}>
                {product.variant.map((item, index) =>{
                    if(item.name == "Fingerprint Title" || item.name == "_Fingerprint File") {
                        return null
                    }
                    return(
                        <Text key={index} style={styles.checkoutDetail}>
                            {item.name + ": "}
                            <Text style={{fontWeight: 'bold'}}>
                                {item.value}
                            </Text>
                        </Text>
                    )
                })}
            </View>

            <View>
                <Text style={styles.singleProductDescription}>{product.description}</Text>
            </View>
            {/* <View style={{marginTop: 25, marginBottom: 35}}>
                <Text style={styles.checkoutDetail}>
                Length:{' '}
                <Text style={{fontWeight: 'bold'}}>
                    {productAttributes['chain-length'] || 'Not Selected'}
                </Text>
                </Text>
                <Text style={styles.checkoutDetail}>
                Metal Color:{' '}
                <Text style={{fontWeight: 'bold'}}>
                    {productAttributes['metal-color'] || 'Not Selected'}
                </Text>
                </Text>
            </View> */}

            
            </Content>
            <View style={{marginBottom:20}}>
            {!isLoading ? <View>
                    <Text style={[styles.singleProductDescription, {textAlign:'center', marginVertical:5}]}>{`Order Number: ${productDetail.orderData.id}`}</Text>
                    <Text style={[styles.singleProductDescription, {textAlign:'center',marginVertical:5}]}>{`Expected Shipping date: ${expectedDeliveryDate}`}</Text>
                </View>:<ActivityIndicator />}
                </View>
        </Container>
        ) : (
        <ActivityIndicator />
        );
    }
}

const mapDispatchToProps = dispatch => ({
    getOrderFulfillmentData : (orderId,fulfillmentsId, callback) => dispatch(getOrderFulfillmentData(orderId, fulfillmentsId,callback))
});

const mapStateToProps = state => ({
	user: state.user,
	products: state.products,
    fingerprints: state.fingerprints,
    orders: state.orders
});

export default connect(mapStateToProps, mapDispatchToProps)(ProductDetails);