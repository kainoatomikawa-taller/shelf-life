/**
 * The Kitchen list (§5.2): perishables grouped by storage location or
 * urgency, with per-item quick actions, and a separate longer-lived
 * pantry/spices view (AC3) so a jar of oregano doesn't compete for
 * attention with milk that's about to turn.
 */

import React, {useState} from 'react';
import {
  ActivityIndicator,
  SectionList,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import type {InventoryItem} from '../../domain/InventoryItem';
import {SingleSelectChips} from '../add-item/components/SingleSelectChips';
import {InventoryItemRow} from './InventoryItemRow';
import {
  groupLongLived,
  groupPerishables,
  selectUseItUpSoon,
  splitPerishablesFromLongLived,
  type GroupBy,
} from './groupInventoryItems';
import {useInventoryItems} from './useInventoryItems';
import {UseItUpSoonStrip} from './UseItUpSoonStrip';

interface Props {
  userId: string;
  displayName: string;
  onCookNow: (item: InventoryItem) => void;
}

type ViewMode = 'kitchen' | 'pantrySpices';

const VIEW_MODES: readonly ViewMode[] = ['kitchen', 'pantrySpices'];
const GROUP_BY_OPTIONS: readonly GroupBy[] = ['location', 'urgency'];

function viewModeLabel(mode: ViewMode): string {
  return mode === 'kitchen' ? 'Kitchen' : 'Pantry & Spices';
}

function groupByLabel(groupBy: GroupBy): string {
  return groupBy === 'location' ? 'By location' : 'By urgency';
}

export function KitchenScreen({
  userId,
  displayName,
  onCookNow,
}: Props): React.JSX.Element {
  const {items, loading, error, setQuantityState, editDates, remove} =
    useInventoryItems(userId);
  const [viewMode, setViewMode] = useState<ViewMode>('kitchen');
  const [groupBy, setGroupBy] = useState<GroupBy>('location');

  const {perishables, longLived} = splitPerishablesFromLongLived(items);
  const sections =
    viewMode === 'kitchen'
      ? groupPerishables(perishables, groupBy)
      : groupLongLived(longLived);
  const useItUpSoon = selectUseItUpSoon(items);

  return (
    <View style={styles.container}>
      <Text style={styles.greeting}>Welcome back, {displayName}</Text>
      <Text style={styles.title}>Kitchen</Text>

      <UseItUpSoonStrip items={useItUpSoon} onCookNow={onCookNow} />

      <SingleSelectChips
        options={VIEW_MODES}
        selected={viewMode}
        onSelect={setViewMode}
        labelFor={viewModeLabel}
      />

      {viewMode === 'kitchen' && (
        <View style={styles.groupByRow}>
          <SingleSelectChips
            options={GROUP_BY_OPTIONS}
            selected={groupBy}
            onSelect={setGroupBy}
            labelFor={groupByLabel}
          />
        </View>
      )}

      {loading && <ActivityIndicator style={styles.spinner} />}
      {error && <Text style={styles.error}>{error}</Text>}

      {!loading && !error && (
        <SectionList
          style={styles.list}
          sections={sections.map(section => ({...section}))}
          keyExtractor={item => item.id}
          renderSectionHeader={({section}) => (
            <Text style={styles.sectionHeader}>
              {section.title} ({section.data.length})
            </Text>
          )}
          renderItem={({item}) => (
            <InventoryItemRow
              item={item}
              onMarkLow={() => void setQuantityState(item.id, 'low')}
              onMarkOut={() => void setQuantityState(item.id, 'out')}
              onUsedItUp={() => void remove(item.id)}
              onDelete={() => void remove(item.id)}
              onSaveDates={dates => void editDates(item.id, dates)}
            />
          )}
          ListEmptyComponent={
            <Text style={styles.empty}>
              {viewMode === 'kitchen'
                ? 'No perishables tracked yet.'
                : 'No pantry or spice items tracked yet.'}
            </Text>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, padding: 20, paddingBottom: 0},
  greeting: {fontSize: 14, fontWeight: '600', color: '#666', marginBottom: 2},
  title: {fontSize: 28, fontWeight: '700', marginBottom: 16},
  groupByRow: {marginTop: 12},
  spinner: {marginTop: 24},
  error: {color: '#c62828', marginTop: 12},
  list: {flex: 1, marginTop: 16},
  sectionHeader: {
    fontSize: 13,
    fontWeight: '700',
    color: '#666',
    backgroundColor: '#fff',
    paddingTop: 12,
    paddingBottom: 6,
    textTransform: 'uppercase',
  },
  empty: {color: '#666', marginTop: 24, textAlign: 'center'},
});
