/**
 * Shared chrome for every onboarding step: progress dots, title/subtitle,
 * scrollable body, and a Skip / Continue footer.
 */

import React from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

interface Props {
  stepNumber: number;
  totalSteps: number;
  title: string;
  subtitle?: string;
  banner?: string;
  continueLabel: string;
  submitting?: boolean;
  onSkip: () => void;
  onContinue: () => void;
  children: React.ReactNode;
}

export function StepShell({
  stepNumber,
  totalSteps,
  title,
  subtitle,
  banner,
  continueLabel,
  submitting,
  onSkip,
  onContinue,
  children,
}: Props): React.JSX.Element {
  return (
    <View style={styles.container}>
      <View style={styles.progressRow}>
        {Array.from({length: totalSteps}, (_, i) => (
          <View
            key={i}
            style={[
              styles.progressDot,
              i < stepNumber && styles.progressDotDone,
            ]}
          />
        ))}
      </View>
      <Text style={styles.stepCount}>
        Step {stepNumber} of {totalSteps}
      </Text>

      <ScrollView
        style={styles.body}
        contentContainerStyle={styles.bodyContent}
        keyboardShouldPersistTaps="handled">
        <Text style={styles.title}>{title}</Text>
        {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
        {banner && (
          <View style={styles.banner}>
            <Text style={styles.bannerText}>{banner}</Text>
          </View>
        )}
        {children}
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity
          onPress={onSkip}
          disabled={submitting}
          style={styles.skipButton}>
          <Text style={styles.skipText}>Skip</Text>
        </TouchableOpacity>
        <TouchableOpacity
          onPress={onContinue}
          disabled={submitting}
          style={styles.continueButton}>
          {submitting ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.continueText}>{continueLabel}</Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, paddingHorizontal: 20, paddingTop: 12},
  progressRow: {flexDirection: 'row', gap: 6, marginBottom: 6},
  progressDot: {flex: 1, height: 4, borderRadius: 2, backgroundColor: '#e0e0e0'},
  progressDotDone: {backgroundColor: '#2e7d32'},
  stepCount: {fontSize: 12, color: '#888', marginBottom: 16},
  body: {flex: 1},
  bodyContent: {paddingBottom: 24},
  title: {fontSize: 24, fontWeight: '700', marginBottom: 8},
  subtitle: {fontSize: 15, color: '#555', marginBottom: 16},
  banner: {
    backgroundColor: '#fff4e5',
    borderLeftWidth: 4,
    borderLeftColor: '#e65100',
    padding: 12,
    borderRadius: 6,
    marginBottom: 20,
  },
  bannerText: {color: '#7a3e00', fontSize: 13, lineHeight: 18},
  footer: {
    flexDirection: 'row',
    gap: 12,
    paddingVertical: 16,
  },
  skipButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ccc',
  },
  skipText: {color: '#555', fontWeight: '600'},
  continueButton: {
    flex: 2,
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
    backgroundColor: '#2e7d32',
  },
  continueText: {color: '#fff', fontWeight: '700'},
});
