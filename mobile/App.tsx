/**
 * Shelf Life — React Native root component.
 * @format
 */

import React, {useState} from 'react';
import {SafeAreaView, StatusBar, StyleSheet} from 'react-native';
import {OnboardingScreen} from './src/ui/onboarding/OnboardingScreen';
import {PantryScreen} from './src/ui/PantryScreen';

const DEMO_USER_ID = 'demo-user';

function App(): React.JSX.Element {
  const [onboarded, setOnboarded] = useState(false);

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar barStyle="dark-content" />
      {onboarded ? (
        <PantryScreen />
      ) : (
        <OnboardingScreen
          userId={DEMO_USER_ID}
          onComplete={() => setOnboarded(true)}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: {flex: 1, backgroundColor: '#fff'},
});

export default App;
