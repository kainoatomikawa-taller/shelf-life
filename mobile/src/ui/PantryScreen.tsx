import React from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import {usePantryItems} from './usePantryItems';
import {PantryItemRow} from './PantryItemRow';

const DEMO_OWNER_ID = 'demo-user';

export function PantryScreen(): React.JSX.Element {
  const {items, loading, error} = usePantryItems(DEMO_OWNER_ID);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Shelf Life</Text>
      {loading && <ActivityIndicator />}
      {error && <Text style={styles.error}>{error}</Text>}
      {!loading && !error && (
        <FlatList
          data={items}
          keyExtractor={item => item.id}
          renderItem={({item}) => <PantryItemRow item={item} />}
          ListEmptyComponent={
            <Text style={styles.empty}>Your pantry is empty.</Text>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, padding: 16, paddingTop: 48},
  title: {fontSize: 28, fontWeight: '700', marginBottom: 16},
  error: {color: '#c62828'},
  empty: {color: '#666', marginTop: 24, textAlign: 'center'},
});
