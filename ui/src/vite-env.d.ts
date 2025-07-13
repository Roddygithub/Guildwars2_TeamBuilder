/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  // Ajoutez d'autres variables d'environnement ici selon vos besoins
  // Exemple:
  // readonly VITE_APP_TITLE: string;
  // readonly VITE_APP_VERSION: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// Déclarations de types pour les modules CSS
// Permet d'importer les fichiers CSS comme des modules TypeScript
declare module '*.module.css' {
  const classes: { [key: string]: string };
  export default classes;
}

declare module '*.module.scss' {
  const classes: { [key: string]: string };
  export default classes;
}

// Déclarations pour les imports d'images
declare module '*.png' {
  const src: string;
  export default src;
}

declare module '*.jpg' {
  const src: string;
  export default src;
}

declare module '*.jpeg' {
  const src: string;
  export default src;
}

declare module '*.gif' {
  const src: string;
  export default src;
}

declare module '*.svg' {
  import * as React from 'react';
  
  export const ReactComponent: React.FunctionComponent<
    React.SVGProps<SVGSVGElement> & { title?: string }
  >;
  
  const src: string;
  export default src;
}

// Déclarations pour les fichiers de données JSON
declare module '*.json' {
  const value: Record<string, unknown>;
  export default value;
}

// Déclaration pour les fichiers de configuration YAML (si vous en utilisez)
declare module '*.yaml' {
  const data: Record<string, unknown>;
  export default data;
}

declare module '*.yml' {
  const data: Record<string, unknown>;
  export default data;
}

// Pour les fichiers Markdown (si vous en utilisez)
declare module '*.md' {
  const content: string;
  export default content;
}

// Pour les fichiers de police
declare module '*.woff' {
  const src: string;
  export default src;
}

declare module '*.woff2' {
  const src: string;
  export default src;
}

declare module '*.ttf' {
  const src: string;
  export default src;
}
