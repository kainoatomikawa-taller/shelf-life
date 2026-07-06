module.exports = {
  root: true,
  extends: ['@react-native', 'prettier'],
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint'],
  rules: {
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/no-unused-vars': ['error', {argsIgnorePattern: '^_'}],
  },
};
