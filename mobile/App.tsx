/**
 * Shelf Life — React Native root component.
 * @format
 */

import React, {useState} from 'react';
import {SafeAreaView, StatusBar, StyleSheet, Text, TouchableOpacity, View} from 'react-native';
import {AddItemScreen} from './src/ui/add-item/AddItemScreen';
import {CookNowScreen} from './src/ui/cook-now/CookNowScreen';
import {DiscoverScreen} from './src/ui/discover/DiscoverScreen';
import {KitchenScreen} from './src/ui/kitchen/KitchenScreen';
import {LoginScreen} from './src/ui/login/LoginScreen';
import {OnboardingScreen} from './src/ui/onboarding/OnboardingScreen';
import {ProfileScreen} from './src/ui/profile/ProfileScreen';
import type {AuthUser} from './src/domain/Auth';

type Tab = 'kitchen' | 'cookNow' | 'discover' | 'add' | 'profile';

function App(): React.JSX.Element {
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [onboarded, setOnboarded] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('kitchen');
  const [cookNowIngredient, setCookNowIngredient] = useState<string | null>(null);

  if (!authUser) {
    return (
      <SafeAreaView style={styles.root}>
        <StatusBar barStyle="dark-content" />
        <LoginScreen onLoggedIn={setAuthUser} />
      </SafeAreaView>
    );
  }

  const userId = authUser.id;

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar barStyle="dark-content" />
      {!onboarded && (
        <OnboardingScreen
          userId={userId}
          onComplete={() => setOnboarded(true)}
        />
      )}
      {onboarded && cookNowIngredient && (
        <CookNowScreen
          userId={userId}
          filterIngredientName={cookNowIngredient}
          onBack={() => setCookNowIngredient(null)}
        />
      )}
      {onboarded && !cookNowIngredient && (
        <>
          {activeTab === 'kitchen' && (
            <KitchenScreen
              userId={userId}
              onCookNow={item => setCookNowIngredient(item.ingredientName)}
            />
          )}
          {activeTab === 'cookNow' && (
            <CookNowScreen
              userId={userId}
              onBack={() => setActiveTab('kitchen')}
            />
          )}
          {activeTab === 'discover' && <DiscoverScreen userId={userId} />}
          {activeTab === 'add' && <AddItemScreen userId={userId} />}
          {activeTab === 'profile' && <ProfileScreen userId={userId} />}
          <View style={styles.tabBar}>
            <TouchableOpacity
              style={styles.tabButton}
              onPress={() => setActiveTab('kitchen')}>
              <Text
                style={[styles.tabLabel, activeTab === 'kitchen' && styles.tabLabelActive]}>
                Kitchen
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.tabButton}
              onPress={() => setActiveTab('cookNow')}>
              <Text
                style={[styles.tabLabel, activeTab === 'cookNow' && styles.tabLabelActive]}>
                Cook Now
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.tabButton}
              onPress={() => setActiveTab('discover')}>
              <Text
                style={[styles.tabLabel, activeTab === 'discover' && styles.tabLabelActive]}>
                Discover
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.tabButton}
              onPress={() => setActiveTab('add')}>
              <Text
                style={[styles.tabLabel, activeTab === 'add' && styles.tabLabelActive]}>
                Add Item
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
