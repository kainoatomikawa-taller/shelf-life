/**
 * A single Kitchen list row (§5.2 AC1): name, quantity state, and the
 * correct labeled freshness date, plus per-item quick actions (AC2) —
 * one-tap Mark Low / Mark Out / used-it-up, edit dates, and delete.
 */

import React, {useState} from 'react';
import {StyleSheet, Text, TouchableOpacity, View} from 'react-native';
import {quantityStateLabel} from '../../domain/Ingredient';
import {freshnessStatusColor, type InventoryItem} from '../../domain/InventoryItem';

interface Props {
  item: InventoryItem;
  onMarkLow: () => void;
  onMarkOut: () => void;
  onUsedItUp: () => void;
  onDelete: () => void;
  onSaveDates: (dates: {
    purchaseDate?: string;
    printedPackageDate?: string;
  }) => void;
}

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

export function InventoryItemRow({
  item,
  onMarkLow,
  onMarkOut,
  onUsedItUp,
  onDelete,
  onSaveDates,
}: Props): React.JSX.Element {
  const [editingDates, setEditingDates] = useState(false);
  const [purchaseDate, setPurchaseDate] = useState(item.purchaseDate ?? undefined);
  const [printedPackageDate, setPrintedPackageDate] = useState(
    item.printedPackageDate ?? undefined,
  );

  function startEditingDates(): void {
    setPurchaseDate(item.purchaseDate ?? undefined);
    setPrintedPackageDate(item.printedPackageDate ?? undefined);
    setEditingDates(true);
  }

  function saveDates(): void {
    onSaveDates({purchaseDate, printedPackageDate});
    setEditingDates(false);
  }

  return (
    <View style={styles.row}>
      <View style={styles.headerLine}>
        <View
          style={[
            styles.dot,
            {backgroundColor: freshnessStatusColor(item.freshnessStatus)},
          ]}
        />
        <Text style={styles.name}>{item.ingredientName}</Text>
        <View style={styles.quantityBadge}>
          <Text style={styles.quantityBadgeText}>
            {quantityStateLabel(item.quantityState)}
          </Text>
        </View>
      </View>

      <Text style={styles.dateLine}>
        {item.freshnessDateLabel}: {item.computedFreshnessDate}
      </Text>
      <Text style={styles.tooltip}>{item.freshnessDateTooltip}</Text>

      {item.spoilageCheckTip && (
        <View style={styles.spoilageTip}>
          <Text style={styles.spoilageTipText}>
            Smell: {item.spoilageCheckTip.smell}
          </Text>
          <Text style={styles.spoilageTipText}>
            Look: {item.spoilageCheckTip.look}
          </Text>
        </View>
      )}

      <View style={styles.actions}>
        <TouchableOpacity style={styles.actionButton} onPress={onMarkLow}>
          <Text style={styles.actionText}>Low</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton} onPress={onMarkOut}>
          <Text style={styles.actionText}>Out</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton} onPress={onUsedItUp}>
          <Text style={styles.actionText}>Used it up</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton} onPress={startEditingDates}>
          <Text style={styles.actionText}>Edit dates</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.actionButton, styles.deleteButton]}
          onPress={onDelete}>
          <Text style={[styles.actionText, styles.deleteText]}>Delete</Text>
        </TouchableOpacity>
      </View>

      {editingDates && (
        <View style={styles.dateEditor}>
          <View style={styles.dateEditorRow}>
            <Text style={styles.dateEditorLabel}>Purchase date</Text>
            <TouchableOpacity
              style={[styles.chip, purchaseDate && styles.chipSelected]}
              onPress={() =>
                setPurchaseDate(current => (current ? undefined : today()))
              }>
              <Text
                style={[styles.chipText, purchaseDate && styles.chipTextSelected]}>
                {purchaseDate ?? 'Not set'}
              </Text>
            </TouchableOpacity>
          </View>
          <View style={styles.dateEditorRow}>
            <Text style={styles.dateEditorLabel}>Package date</Text>
            <TouchableOpacity
              style={[styles.chip, printedPackageDate && styles.chipSelected]}
              onPress={() =>
                setPrintedPackageDate(current => (current ? undefined : today()))
              }>
              <Text
                style={[
                  styles.chipText,
                  printedPackageDate && styles.chipTextSelected,
                ]}>
                {printedPackageDate ?? 'Not set'}
              </Text>
            </TouchableOpacity>
          </View>
          <View style={styles.dateEditorFooter}>
            <TouchableOpacity onPress={() => setEditingDates(false)}>
              <Text style={styles.cancelLink}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.saveButton} onPress={saveDates}>
              <Text style={styles.saveButtonText}>Save</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  headerLine: {flexDirection: 'row', alignItems: 'center'},
  dot: {width: 10, height: 10, borderRadius: 5, marginRight: 10},
  name: {flex: 1, fontSize: 16, fontWeight: '600'},
  quantityBadge: {
    backgroundColor: '#eef5ee',
    borderRadius: 12,
    paddingVertical: 3,
    paddingHorizontal: 10,
  },
  quantityBadgeText: {fontSize: 12, color: '#2e7d32', fontWeight: '600'},
  dateLine: {fontSize: 13, color: '#333', marginTop: 6, marginLeft: 20},
  tooltip: {fontSize: 11, color: '#888', marginTop: 2, marginLeft: 20},
  spoilageTip: {
    marginTop: 8,
    marginLeft: 20,
    backgroundColor: '#fff4e5',
    borderRadius: 6,
    padding: 8,
  },
  spoilageTipText: {fontSize: 11, color: '#7a3e00', lineHeight: 15},
  actions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 10,
    marginLeft: 20,
  },
  actionButton: {
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#ccc',
  },
  actionText: {fontSize: 12, color: '#333', fontWeight: '600'},
  deleteButton: {borderColor: '#e0b4b4'},
  deleteText: {color: '#c62828'},
  dateEditor: {
    marginTop: 10,
    marginLeft: 20,
    backgroundColor: '#fafafa',
    borderRadius: 8,
    padding: 10,
  },
  dateEditorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  dateEditorLabel: {fontSize: 12, color: '#555'},
  chip: {
    paddingVertical: 5,
    paddingHorizontal: 12,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#ccc',
    backgroundColor: '#fff',
  },
  chipSelected: {backgroundColor: '#2e7d32', borderColor: '#2e7d32'},
  chipText: {fontSize: 12, color: '#333'},
  chipTextSelected: {color: '#fff', fontWeight: '600'},
  dateEditorFooter: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    alignItems: 'center',
    gap: 16,
  },
  cancelLink: {fontSize: 13, color: '#888'},
  saveButton: {
    backgroundColor: '#2e7d32',
    borderRadius: 8,
    paddingVertical: 6,
    paddingHorizontal: 14,
  },
  saveButtonText: {color: '#fff', fontWeight: '700', fontSize: 13},
});
