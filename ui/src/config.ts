// Configuration de l'application
export const config = {
  // URL de l'API backend
  api: {
    baseUrl: 'http://localhost:8000/api',
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
    population: 150,
    samples: 1000 // Nombre de combinaisons testées pour l'optimisation
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
