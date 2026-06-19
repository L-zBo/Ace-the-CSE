import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.ace.cse',
  appName: 'Ace the CSE',
  webDir: 'out',
  server: {
    androidScheme: 'https',
  },
  android: {
    backgroundColor: '#000000',
    allowMixedContent: true,
  },
};

export default config;
