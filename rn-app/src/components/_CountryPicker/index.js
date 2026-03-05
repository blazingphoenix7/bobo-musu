import React from 'react';
import { Image, Modal, FlatList, TouchableOpacity, StyleSheet, I18nManager, TextInput, Keyboard } from "react-native";
import { View, Text, Header, Container, Label, Body, Left, Right, Icon, } from 'native-base';

import * as colors from '../../styles/colors'
import Flags from "./flags";
const countries = require("./countries.json");

class _CountryPicker extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            modalVisible: false,
            selectedCountry: props.selectedCountry,
            searchCountry: '',
            filterCountries: countries
        }
    }

    static getDerivedStateFromProps(props, state){
		return {
            selectedCountry: props.selectedCountry,
        }
	}

    searchCountry = (searchCountry) => {
        this.setState({ searchCountry })
        const filterCountries = countries.filter(item => {
            const itemData = `${item.name.toUpperCase()} ${"+" + item.dialCode}`;
            const textData = searchCountry.toUpperCase();
            return itemData.indexOf(textData) > -1;
        });

        this.setState({ filterCountries: filterCountries });
    }

    renderCountryList() {
        
        return (
            <Modal
                animationType="slide"
                transparent={false}
                visible={this.state.modalVisible}
                onRequestClose={() => this.setState({ modalVisible: false })}>
                <Container>
                    <Header style={{ backgroundColor: colors.secondaryTextColor }}>
                        <Left style={{}} >
                            <Icon type={"AntDesign"} name={(I18nManager.isRTL) ? "arrowright" : "arrowleft"} size={25} style={{ marginLeft: 10, color: colors.black }} onPress={() => this.selectCountry(this.state.selectedCountry)} />
                        </Left>
                        <Body style={{ width: '100%', flex: 1 }}>
                            <Label>{"Select Country"}</Label>
                        </Body>
                        <Right />
                    </Header>
                    <TextInput style={styles.textInputStyle}
                        ref={"countrySearchInput"}
                        placeholder={"Search Country"}
                        placeholderTextColor={colors.darkColor}
                        value={this.state.searchCountry}
                        onChangeText={this.searchCountry}
                        autoCapitalize={"none"}
                        returnKeyType={"search"}
                        onSubmitEditing={() => Keyboard.dismiss()}
                    />
                    <FlatList
                        data={this.state.filterCountries}
                        renderItem={this.renderItem}
                        extraData={this.state}
                        keyExtractor={(item, index) => index.toString()}
                    />
                </Container>
            </Modal>
        )

    }

    renderItem = (data) => {
        let item = data.item;
        return (
            <TouchableOpacity style={{ flexDirection: 'row', margin: 10, alignItems: 'center' }} onPress={() => this.selectCountry(item)}>
                <Image resizeMode={"contain"} style={{ width: 25, height: 20, marginTop: -5 }} source={Flags.get(item.iso2)} />
                <Text style={{ flex: 1, marginHorizontal: 10, fontSize: 12, color: colors.darkColor }}>{item.name + `(+${item.dialCode})`}</Text>
                {this.state.selectedCountry.iso2 == item.iso2 && <Icon type={"MaterialIcons"} name={"done"} style={{ color: colors.darkColor }} size={20} />}
            </TouchableOpacity>
        )
    }

    selectCountry(item) {
        this.setState({
            modalVisible: false,
            searchCountry: '',
            selectedCountry: item,
            filterCountries: countries
        })
        this.props.onValueChange(item);
    }

    render() {
        return (
            <View >
                {this.renderCountryList()}
                <TouchableOpacity style={{ flexDirection: 'row', alignItems: 'flex-end' }} onPress={() => this.setState({ modalVisible: true })}>
                    <Image resizeMode={"contain"} style={{ width: 20, height: 15, marginTop: -5 }} source={Flags.get(this.state.selectedCountry.iso2)} />
                    <Icon type={"AntDesign"} name={"caretdown"} style={{ marginHorizontal: 5, color: colors.darkColor, fontSize: 8 }} />
                    <Text style={{ fontSize: 12, color: colors.darkColor }}>{"(+" + this.state.selectedCountry.dialCode + ")"}</Text>
                </TouchableOpacity>
            </View>
        )
    }
}

export default _CountryPicker;

const styles = StyleSheet.create({
    textInputStyle: {
        color: colors.darkColor,
        borderWidth: StyleSheet.hairlineWidth,
        borderColor: colors.gray_dark,
        paddingHorizontal: 5,
        height: 40,
        width: '100%',
        fontFamily: 'Avenir',
        fontSize: 13,
        textAlign: I18nManager.isRTL ? 'right' : 'left'
    },
})