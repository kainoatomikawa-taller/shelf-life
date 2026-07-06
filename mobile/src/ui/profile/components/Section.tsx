/**
 * A titled, visually separated block within the profile settings screen.
 */

import React from 'react';
import {StyleSheet, Text, View} from 'react-native';

interface Props {
  title: string;
  subtitle?: string;
  banner?: string;
  children: React.ReactNode;
}

export function Section({title, subtitle, banner, children}: Props): React.JSX.Element {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>{title}</Text>
      {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
      {banner && (
        <View style={styles.banner}>
          <Text style={styles.bannerText}>{banner}</Text>
        </View>
      )}
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 28,
    paddingBottom: 24,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  title: {fontSize: 18, fontWeight: '700', marginBottom: 6},
  subtitle: {fontSize: 13, color: '#555', marginBottom: 12},
  banner: {
    backgroundColor: '#fff4e5',
    borderLeftWidth: 4,
    borderLeftColor: '#e65100',
    padding: 12,
    borderRadius: 6,
    marginBottom: 16,
  },
  bannerText: {color: '#7a3e00', fontSize: 13, lineHeight: 18},
});
