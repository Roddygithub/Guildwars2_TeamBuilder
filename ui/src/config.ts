// Configuration de l'application
export const config = {
  // URL de l'API backend
  api: {
    baseUrl: 'http://localhost:8001',
    endpoints: {
      teams: {
        generate: '/teams/generate'
      }
    }
  },
  
  // Paramètres par défaut
  defaults: {
    teamSize: 5,
    playstyle: 'zerg',
    generations: 50,
    population: 150
  },
  
  // Options pour les styles de jeu
  playstyles: [
    { value: 'zerg', label: 'Zerg (grands groupes)' },
    { value: 'havoc', label: 'Havoc (petits groupes organisés)' },
    { value: 'roaming', label: 'Roaming (petits groupes mobiles)' },
    { value: 'gvg', label: 'GvG (affrontements de guilde)' }
  ]
};

export default config;
