/**
 * Add-item screen (§5.2): search the ingredient catalog (with alias
 * support), then confirm smart defaults derived from the chosen
 * ingredient's category. Only the ingredient is required — storage
 * location, purchase date, package date and quantity state are all
 * skippable, one-tap fields.
 */

import React, {useState} from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import {InventoryApi} from '../../data/InventoryApi';
import {
  matchedAlias,
  QUANTITY_STATES,
  quantityStateLabel,
  STORAGE_LOCATIONS,
  storageLocationLabel,
  type IngredientSummary,
  type QuantityState,
  type StorageLocation,
} from '../../domain/Ingredient';
import {SingleSelectChips} from './components/SingleSelectChips';
import {useIngredientSearch} from './useIngredientSearch';

interface Props {
  userId: string;
}

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

const api = new InventoryApi();

export function AddItemScreen({userId}: Props): React.JSX.Element {
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState<IngredientSummary | null>(null);
  const [quantityState, setQuantityState] = useState<QuantityState>('in');
  const [storageLocation, setStorageLocation] = useState<StorageLocation | null>(
    null,
  );
  const [boughtToday, setBoughtToday] = useState(false);
  const [datedToday, setDatedToday] = useState(false);
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmation, setConfirmation] = useState<string | null>(null);

  const {results, loading, error: searchError} = useIngredientSearch(query);

  const effectiveStorageLocation: StorageLocation =
    storageLocation ?? selected?.defaultStorageLocation ?? 'fridge';

  function selectIngredient(ingredient: IngredientSummary): void {
    setSelected(ingredient);
    setQuery('');
    setQuantityState('in');
    setStorageLocation(null);
    setBoughtToday(false);
    setDatedToday(false);
    setError(null);
    setConfirmation(null);
  }

  function changeIngredient(): void {
    setSelected(null);
    setError(null);
  }

  async function handleAdd(): Promise<void> {
    if (!selected) {
      return;
    }
    setAdding(true);
    setError(null);
    try {
      const item = await api.add({
        userId,
        ingredientId: selected.id,
        quantityState,
        storageLocation: effectiveStorageLocation,
        purchaseDate: boughtToday ? today() : undefined,
        printedPackageDate: datedToday ? today() : undefined,
        isFrozen: effectiveStorageLocation === 'freezer',
      });
      setConfirmation(
        `Added ${item.ingredientName} to your ${storageLocationLabel(
          item.storageLocation,
        ).toLowerCase()}.`,
      );
      changeIngredient();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setAdding(false);
    }
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled">
      <Text style={styles.title}>Add an item</Text>
      {confirmation && <Text style={styles.confirmation}>{confirmation}</Text>}

      {!selected && (
        <>
          <TextInput
            value={query}
            onChangeText={text => {
              setQuery(text);
              setConfirmation(null);
            }}
            placeholder="Search ingredients (try “scallion”)"
            style={styles.input}
            autoCapitalize="none"
            autoCorrect={false}
          />
          {loading && <ActivityIndicator style={styles.spinner} />}
          {searchError && <Text style={styles.error}>{searchError}</Text>}
          {!loading && query.trim().length > 0 && results.length === 0 && (
            <Text style={styles.empty}>No ingredients found for “{query}”.</Text>
          )}
          {results.map(ingredient => {
            const alias = matchedAlias(ingredient, query);
            return (
              <TouchableOpacity
                key={ingredient.id}
                style={styles.resultRow}
                onPress={() => selectIngredient(ingredient)}>
                <Text style={styles.resultName}>{ingredient.name}</Text>
                {alias && (
                  <Text style={styles.resultAlias}>matched “{alias}”</Text>
                )}
              </TouchableOpacity>
            );
          })}
        </>
      )}

      {selected && (
        <View>
          <View style={styles.selectedRow}>
            <Text style={styles.selectedName}>{selected.name}</Text>
            <TouchableOpacity onPress={changeIngredient}>
              <Text style={styles.changeLink}>Change</Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.sectionLabel}>Storage location</Text>
          <Text style={styles.sectionHint}>
            Suggested from category: {storageLocationLabel(selected.defaultStorageLocation)}
          </Text>
          <SingleSelectChips
            options={STORAGE_LOCATIONS}
            selected={effectiveStorageLocation}
            onSelect={setStorageLocation}
            labelFor={storageLocationLabel}
          />

          <Text style={styles.sectionLabel}>How much do you have?</Text>
          <SingleSelectChips
            options={QUANTITY_STATES}
            selected={quantityState}
            onSelect={setQuantityState}
            labelFor={quantityStateLabel}
          />

          <Text style={styles.sectionLabel}>Purchase date (optional)</Text>
          <TouchableOpacity
            style={[styles.chip, boughtToday && styles.chipSelected]}
            onPress={() => setBoughtToday(v => !v)}>
            <Text style={[styles.chipText, boughtToday && styles.chipTextSelected]}>
              Bought today
            </Text>
          </TouchableOpacity>

          <Text style={styles.sectionLabel}>Package date (optional)</Text>
          <TouchableOpacity
            style={[styles.chip, datedToday && styles.chipSelected]}
            onPress={() => setDatedToday(v => !v)}>
            <Text style={[styles.chipText, datedToday && styles.chipTextSelected]}>
              Dated today
            </Text>
          </TouchableOpacity>

          {error && <Text style={styles.error}>{error}</Text>}

          <TouchableOpacity
            style={styles.addButton}
            disabled={adding}
            onPress={() => void handleAdd()}>
            {adding ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.addButtonText}>Add to inventory</Text>
            )}
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1},
  content: {padding: 20, paddingBottom: 48},
  title: {fontSize: 28, fontWeight: '700', marginBottom: 16},
  confirmation: {
    color: '#2e7d32',
    backgroundColor: '#eef5ee',
    padding: 10,
    borderRadius: 8,
    marginBottom: 16,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
  },
  spinner: {marginTop: 12},
  error: {color: '#c62828', marginTop: 8},
  empty: {color: '#666', marginTop: 16},
  resultRow: {
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  resultName: {fontSize: 16, fontWeight: '600'},
  resultAlias: {fontSize: 12, color: '#888', marginTop: 2},
  selectedRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  selectedName: {fontSize: 22, fontWeight: '700'},
  changeLink: {color: '#2e7d32', fontWeight: '600'},
  sectionLabel: {fontSize: 14, fontWeight: '600', marginTop: 16, marginBottom: 4},
  sectionHint: {fontSize: 12, color: '#888', marginBottom: 8},
  chip: {
    alignSelf: 'flex-start',
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#ccc',
    backgroundColor: '#fff',
  },
  chipSelected: {backgroundColor: '#2e7d32', borderColor: '#2e7d32'},
  chipText: {color: '#333', fontSize: 14},
  chipTextSelected: {color: '#fff', fontWeight: '600'},
  addButton: {
    marginTop: 28,
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
    backgroundColor: '#2e7d32',
  },
  addButtonText: {color: '#fff', fontWeight: '700', fontSize: 16},
});
