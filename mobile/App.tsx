/**
 * Shelf Life — React Native root component.
 * @format
 */

import React, {useState} from 'react';
import {
  ActivityIndicator,
  SafeAreaView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import {AddItemScreen} from './src/ui/add-item/AddItemScreen';
import {CookNowScreen} from './src/ui/cook-now/CookNowScreen';
import {DiscoverScreen} from './src/ui/discover/DiscoverScreen';
import {ForgotPasswordScreen} from './src/ui/forgot-password/ForgotPasswordScreen';
import {KitchenScreen} from './src/ui/kitchen/KitchenScreen';
import {LoginScreen} from './src/ui/login/LoginScreen';
import {SignUpScreen} from './src/ui/sign-up/SignUpScreen';
import {OnboardingScreen} from './src/ui/onboarding/OnboardingScreen';
import {ProfileScreen} from './src/ui/profile/ProfileScreen';
import {useAppSession} from './src/ui/useAppSession';

type Tab = 'kitchen' | 'cookNow' | 'discover' | 'add' | 'profile';
type AuthMode = 'login' | 'signUp' | 'forgotPassword';

function App(): React.JSX.Element {
  const {
    checkingSession,
    authUser,
    onboarded,
    setOnboarded,
    signIn,
    updateIdentity,
  } = useAppSession();
  const [authMode, setAuthMode] = useState<AuthMode>('login');
  const [activeTab, setActiveTab] = useState<Tab>('kitchen');
  const [cookNowIngredient, setCookNowIngredient] = useState<string | null>(null);

  if (checkingSession) {
    return (
      <SafeAreaView style={styles.root}>
        <StatusBar barStyle="dark-content" />
        <View style={styles.centered}>
          <ActivityIndicator size="large" />
        </View>
      </SafeAreaView>
    );
  }

  if (!authUser) {
    return (
      <SafeAreaView style={styles.root}>
        <StatusBar barStyle="dark-content" />
        {authMode === 'login' && (
          <LoginScreen
            onLoggedIn={signIn}
            onSwitchToSignUp={() => setAuthMode('signUp')}
            onForgotPassword={() => setAuthMode('forgotPassword')}
          />
        )}
        {authMode === 'signUp' && (
          <SignUpScreen
            onSignedUp={signIn}
            onSwitchToLogin={() => setAuthMode('login')}
          />
        )}
        {authMode === 'forgotPassword' && (
          <ForgotPasswordScreen onBackToLogin={() => setAuthMode('login')} />
        )}
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar barStyle="dark-content" />
      {!onboarded && (
        <OnboardingScreen onComplete={() => setOnboarded(true)} />
      )}
      {onboarded && cookNowIngredient && (
        <CookNowScreen
          filterIngredientName={cookNowIngredient}
          onBack={() => setCookNowIngredient(null)}
        />
      )}
      {onboarded && !cookNowIngredient && (
        <>
          {activeTab === 'kitchen' && (
            <KitchenScreen
              displayName={authUser.name}
              onCookNow={item => setCookNowIngredient(item.ingredientName)}
            />
          )}
          {activeTab === 'cookNow' && (
            <CookNowScreen onBack={() => setActiveTab('kitchen')} />
          )}
          {activeTab === 'discover' && <DiscoverScreen />}
          {activeTab === 'add' && <AddItemScreen />}
          {activeTab === 'profile' && (
            <ProfileScreen
              authUser={authUser}
              onIdentityUpdated={updateIdentity}
            />
          )}
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
  centered: {flex: 1, alignItems: 'center', justifyContent: 'center'},
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
