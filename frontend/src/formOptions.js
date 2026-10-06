// shared with backend/helpers.py's CURRENCY_OPTIONS / DECIMAL_SEPARATOR_OPTIONS -- keep in sync
export const CURRENCY_OPTIONS = [
  { value: 'KSh', label: 'KSh Kenyan Shilling' },
  { value: '€', label: '€ Euro' },
  { value: '$', label: '$ Dollar' },
  { value: '£', label: '£ Pound' },
  { value: '', label: 'No currency' },
]

export const DECIMAL_SEPARATOR_OPTIONS = [
  { value: ',', label: ', (comma)' },
  { value: '.', label: '. (period)' },
  { value: 'round', label: 'Round to whole number' },
]
