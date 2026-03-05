import React, { Component } from 'react';
import { TouchableOpacity, Image, View, Platform, Text } from 'react-native';
import { Header, Left, Right, Body, Title } from 'native-base';
import { useSelector } from 'react-redux'
import * as Colors from '../styles/colors'
import { MenuIcon } from './icons';

export default _Header = (props) => {
    
    const cartCount = useSelector((state) => state.orders.cartCount)
    
    return(
        <Header iosBarStyle={'dark-content'} androidStatusBarColor={"#fff"} style={{backgroundColor:'#fff', borderBottomWidth:0, marginTop: Platform.OS == 'ios' ? 0 : 20, marginBottom: Platform.OS == 'ios' ? 0 : 20 }} transparent>
            <Left style={{flex:0.2, alignItems:'center',justifyContent:'center'}}>
                {props.isMenu ? <TouchableOpacity onPress={() => props.navigation.openDrawer()} style={{height: 44, width: 44, alignItems:'center', justifyContent:'center'}}>
                    <Image source={require('../assets/icons/icon-menu.png')} resizeMode={'contain'} style={{height: 25, width: 25}} />
                </TouchableOpacity>
                :
                <TouchableOpacity onPress={() => props.onPress && props.onPress() || props.navigation.goBack()}>
                    <Image source={require('../assets/icons/left-arrow.png')} resizeMode={'contain'} style={{height: 20, width: 30}} />
                </TouchableOpacity>}
            </Left>
            <Body style={{flex:1,alignItems:'center', justifyContent:'center'}}>
                {props.title ?
                    <View>
                        <Title style={{color:'#000'}}>{props.title}</Title>
                    </View>
                    :
                    <View>
                        <Image source={require('../assets/images/logo-row.png')} resizeMode={'contain'} style={{height: 50}} />
                    </View>
                }
            </Body>
            <Right style={{flex:0.2, alignItems:'center',justifyContent:'center'}}>
                
                    {(props.isCart && cartCount > 0) && <TouchableOpacity onPress={() => props.navigation.navigate('Checkout')} style={{backgroundColor:Colors.badgesCBackgroundColor, height: 20, width: 20, borderRadius: 10, alignItems:'center', justifyContent:'center', position:'absolute', zIndex: 1, top:-5, right: 0}}><Text style={{color: Colors.secondaryTextColor, fontFamily: 'Avenir',}}>{cartCount}</Text></TouchableOpacity>}
                    {props.isCart ? 
                    <TouchableOpacity disabled={cartCount == 0} onPress={() => props.navigation.navigate('Checkout')}>
                        <Image source={require('../assets/icons/icon-cart.png')} resizeMode={'contain'} style={{height: 32, width: 32}} />
                    </TouchableOpacity>
                    : null}
                
            </Right>
            
        </Header>
    )
}