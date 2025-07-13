import { visualizer } from 'rollup-plugin-visualizer';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import checker from 'vite-plugin-checker';

export default defineConfig(({ mode }) => {
  // Charge les variables d'environnement en fonction du mode (dev/prod)
  const env = loadEnv(mode, process.cwd(), '');
  const isProduction = mode === 'production';
  
  // Détermine l'URL de l'API en fonction de l'environnement
  const apiUrl = isProduction ? '/api' : env.VITE_API_URL || 'http://localhost:8001';
  
  // Plugins communs
  const plugins = [
    react({
      babel: {
        plugins: [
          ['@babel/plugin-proposal-decorators', { legacy: true }],
          ['@babel/plugin-proposal-class-properties', { loose: true }],
        ],
      },
    }),
    
    // Vérification des types et du linting pendant le développement
    !isProduction && checker({
      // TypeScript
      typescript: {
        tsconfigPath: './tsconfig.json',
        buildMode: true,
      },
      // Vérification du code avec ESLint
      eslint: {
        lintCommand: 'eslint . --ext .ts,.tsx',
        dev: {
          logLevel: ['error'],
        },
      },
      // Vérification des erreurs de compilation
      overlay: {
        initialIsOpen: 'error',
        position: 'br',
        badgeStyle: 'transform: scale(0.8) translateY(4px);',
      },
      enableBuild: true,
    }),
    
    // Analyse du bundle en production
    isProduction && visualizer({
      open: false,
      filename: 'bundle-analysis.html',
      gzipSize: true,
      brotliSize: true,
    })
  ].filter(Boolean); // Filtre les valeurs falsy (false, undefined, etc.)
  
  return {
    plugins,
    // Exposition des variables d'environnement au code client
    define: {
      'process.env': {
        NODE_ENV: JSON.stringify(mode),
        VITE_API_URL: JSON.stringify(apiUrl),
      },
    },
    // Configuration du serveur de développement
    server: {
      port: 5173,
      strictPort: true,
      proxy: {
        '/api': {
          target: apiUrl,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, isProduction ? '' : ''),
          secure: false,
          ws: true,
        },
      },
    },
    // Configuration de la construction
    build: {
      outDir: 'dist',
      emptyOutDir: true,
      sourcemap: !isProduction ? 'inline' : false,
      minify: isProduction ? 'esbuild' : false,
      chunkSizeWarningLimit: 1000, // en Ko
      cssCodeSplit: true,
      reportCompressedSize: false, // Désactive le rapport de taille compressée (plus rapide)
      commonjsOptions: {
        include: [/node_modules/],
        transformMixedEsModules: true,
      },
      rollupOptions: {
        output: {
          manualChunks: {
            react: ['react', 'react-dom', 'react-router-dom'],
            chakra: ['@chakra-ui/react', '@emotion/react', '@emotion/styled', 'framer-motion'],
          },
        },
      },
    },
    // Configuration de l'optimisation pour la production
    optimizeDeps: {
      include: ['react', 'react-dom', 'react-router-dom', '@chakra-ui/react'],
    },
  };
});
