import React from 'react';
import {View, Text} from 'react-native';
import {Provider as ReduxProvider} from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react'
import * as Sentry from '@sentry/react-native';

import {store, persistor} from './src/redux/store';
import NavigatorProvider from './src/navigator';
import {setupHttpConfig} from './src/utils/http';
import * as NavigationService from './src/navigator/NavigationService';

Sentry.init({ 
  dsn: 'https://b485f6b6f8db495a95421d1af8f30bf8@o426030.ingest.sentry.io/5367341', 
});

export default class App extends React.Component {
  state = {
    isLoaded: false,
  };

  async componentDidMount() {
    await this.loadAssets();
    setupHttpConfig();

    /**
     * Read above commments above adding async requests here
     */
    NavigationService.setNavigator(this.navigator);
  }

  loadAssets = async () => {
    // add any loading assets here
    this.setState({ isLoaded: true });
  };

  renderLoading = () => (
    <View style={{ flex: 1 }}>
      <Text>Loading</Text>
    </View>
  );

  renderApp = () => (
    <ReduxProvider store={store}>
      <PersistGate loading={null} persistor={persistor}>
        <NavigatorProvider />
      </PersistGate>
    </ReduxProvider>
  );

  render = () => this.state.isLoaded ? this.renderApp() : this.renderLoading();
}