/**
 * Shelf Life — React Native root component.
 * @format
 */

import React, {useState} from 'react';
import {SafeAreaView, StatusBar, StyleSheet, Text, TouchableOpacity, View} from 'react-native';
import {OnboardingScreen} from './src/ui/onboarding/OnboardingScreen';
import {PantryScreen} from './src/ui/PantryScreen';
import {ProfileScreen} from './src/ui/profile/ProfileScreen';

const DEMO_USER_ID = 'demo-user';

type Tab = 'pantry' | 'profile';

function App(): React.JSX.Element {
  const [onboarded, setOnboarded] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('pantry');

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar barStyle="dark-content" />
      {onboarded ? (
        <>
          {activeTab === 'pantry' ? (
            <PantryScreen />
          ) : (
            <ProfileScreen userId={DEMO_USER_ID} />
          )}
          <View style={styles.tabBar}>
            <TouchableOpacity
              style={styles.tabButton}
              onPress={() => setActiveTab('pantry')}>
              <Text
                style={[styles.tabLabel, activeTab === 'pantry' && styles.tabLabelActive]}>
                Pantry
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.tabButton}
              onPress={() => setActiveTab('profile')}>
              <Text
                style={[
                  styles.tabLabel,
                  activeTab === 'profile' && styles.tabLabelActive,
                ]}>
                Profile
              </Text>
            </TouchableOpacity>
          </View>
        </>
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
  tabBar: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  tabButton: {flex: 1, paddingVertical: 14, alignItems: 'center'},
  tabLabel: {fontSize: 14, color: '#999', fontWeight: '600'},
  tabLabelActive: {color: '#2e7d32'},
});

export default App;
