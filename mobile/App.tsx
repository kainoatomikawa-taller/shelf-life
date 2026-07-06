/**
 * Shelf Life — React Native root component.
 * @format
 */

import React, {useState} from 'react';
import {SafeAreaView, StatusBar, StyleSheet, Text, TouchableOpacity, View} from 'react-native';
import {AddItemScreen} from './src/ui/add-item/AddItemScreen';
import {CookNowScreen} from './src/ui/cook-now/CookNowScreen';
import {KitchenScreen} from './src/ui/kitchen/KitchenScreen';
import {OnboardingScreen} from './src/ui/onboarding/OnboardingScreen';
import {ProfileScreen} from './src/ui/profile/ProfileScreen';

const DEMO_USER_ID = 'demo-user';

type Tab = 'kitchen' | 'cookNow' | 'add' | 'profile';

function App(): React.JSX.Element {
  const [onboarded, setOnboarded] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('kitchen');
  const [cookNowIngredient, setCookNowIngredient] = useState<string | null>(null);

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar barStyle="dark-content" />
      {!onboarded && (
        <OnboardingScreen
          userId={DEMO_USER_ID}
          onComplete={() => setOnboarded(true)}
        />
      )}
      {onboarded && cookNowIngredient && (
        <CookNowScreen
          userId={DEMO_USER_ID}
          filterIngredientName={cookNowIngredient}
          onBack={() => setCookNowIngredient(null)}
        />
      )}
      {onboarded && !cookNowIngredient && (
        <>
          {activeTab === 'kitchen' && (
            <KitchenScreen
              userId={DEMO_USER_ID}
              onCookNow={item => setCookNowIngredient(item.ingredientName)}
            />
          )}
          {activeTab === 'cookNow' && (
            <CookNowScreen
              userId={DEMO_USER_ID}
              onBack={() => setActiveTab('kitchen')}
            />
          )}
          {activeTab === 'add' && <AddItemScreen userId={DEMO_USER_ID} />}
          {activeTab === 'profile' && <ProfileScreen userId={DEMO_USER_ID} />}
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
