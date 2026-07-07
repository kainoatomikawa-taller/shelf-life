/**
 * Profile tab (§6): every field collected during onboarding is editable
 * here, plus a read-only view of the taste vector ratings have shaped.
 * Every edit saves immediately — allergy and diet changes must take effect
 * right away since they gate which recipes are ever safe to suggest.
 */

import React from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import type {AuthUser} from '../../domain/Auth';
import {AdventurousnessStep} from '../onboarding/steps/AdventurousnessStep';
import {AllergiesDietStep} from '../onboarding/steps/AllergiesDietStep';
import {CookingRealityStep} from '../onboarding/steps/CookingRealityStep';
import {CuisinesStep} from '../onboarding/steps/CuisinesStep';
import {FlavorSlidersStep} from '../onboarding/steps/FlavorSlidersStep';
import {AccountSection} from './components/AccountSection';
import {Section} from './components/Section';
import {TasteVectorHistory} from './components/TasteVectorHistory';
import {useAccountProfile} from './useAccountProfile';
import {useProfile} from './useProfile';

interface Props {
  authUser: AuthUser;
  onIdentityUpdated: (
    partial: Partial<Pick<AuthUser, 'username' | 'name'>>,
  ) => void;
}

export function ProfileScreen({
  authUser,
  onIdentityUpdated,
}: Props): React.JSX.Element {
  const {answers, tasteVector, loading, saving, error, updateAnswers} =
    useProfile(authUser.id);
  const {
    username,
    setUsername,
    displayName,
    setDisplayName,
    savingUsername,
    savingDisplayName,
    usernameError,
    displayNameError,
    saveUsername,
    saveDisplayName,
  } = useAccountProfile(authUser, onIdentityUpdated);

  if (loading || !answers || !tasteVector) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled">
      <View style={styles.header}>
        <Text style={styles.title}>Profile</Text>
        {saving && <Text style={styles.status}>Saving…</Text>}
      </View>
      {error && <Text style={styles.error}>{error}</Text>}

      <Section title="Account" subtitle="Your display name and username.">
        <AccountSection
          displayName={displayName}
          onChangeDisplayName={setDisplayName}
          onSaveDisplayName={() => void saveDisplayName()}
          savingDisplayName={savingDisplayName}
          displayNameError={displayNameError}
          username={username}
          onChangeUsername={setUsername}
          onSaveUsername={() => void saveUsername()}
          savingUsername={savingUsername}
          usernameError={usernameError}
        />
      </Section>

      <Section
        title="Allergies & diet"
        banner="For your safety: a recipe that conflicts with an allergy or diet you list here will never be suggested to you, no matter how well it otherwise matches your taste. Changes here take effect immediately.">
        <AllergiesDietStep answers={answers} onChange={updateAnswers} />
      </Section>

      <Section
        title="What you love to eat"
        subtitle="Cuisines and dishes you crave.">
        <CuisinesStep answers={answers} onChange={updateAnswers} />
      </Section>

      <Section
        title="Flavor profile"
        subtitle="Nudge each slider toward how you like your food to taste.">
        <FlavorSlidersStep answers={answers} onChange={updateAnswers} />
      </Section>

      <Section
        title="Cooking reality"
        subtitle="Your skill, time, tools, and budget.">
        <CookingRealityStep answers={answers} onChange={updateAnswers} />
      </Section>

      <Section
        title="Adventurousness"
        subtitle="How far outside your comfort zone should we push?">
        <AdventurousnessStep answers={answers} onChange={updateAnswers} />
      </Section>

      <Section
        title="Ratings history"
        subtitle="Your taste profile, shaped by the recipes you've rated.">
        <TasteVectorHistory tasteVector={tasteVector} />
      </Section>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1},
  content: {padding: 20, paddingBottom: 48},
  centered: {flex: 1, alignItems: 'center', justifyContent: 'center'},
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  title: {fontSize: 28, fontWeight: '700'},
  status: {fontSize: 13, color: '#888'},
  error: {color: '#c62828', marginBottom: 12},
});
