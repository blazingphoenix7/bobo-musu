import React from 'react';
import { Text, View } from 'react-native';

import styles from './styles';

export default function ErrorBox({ errorText }) {
  return (
    <View style={styles.container}>
      <Text category="s1" status="danger" styles={styles.errorText}>
        {errorText}
      </Text>
    </View>
  );
}