document.addEventListener('DOMContentLoaded', () => {
    // Fonction pour générer une équipe
    document.getElementById('generateBtn').addEventListener('click', generateTeam);

    async function generateTeam() {
        const teamSize = parseInt(document.getElementById('teamSize').value);
        const playstyle = document.getElementById('playstyle').value;
        
        // Afficher un indicateur de chargement
        const teamComposition = document.getElementById('teamComposition');
        teamComposition.innerHTML = '<div class="loading">Génération de l\'équipe en cours...</div>';
        
        try {
            // Appel à l'API pour générer une équipe
            const response = await fetch('/api/teams/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    team_size: teamSize,
                    playstyle: playstyle
                })
            });
            
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.teams && data.teams.length > 0) {
                const team = data.teams[0]; // On prend la première équipe générée
                displayTeam(team);
                
                // Afficher le score
                const scoreElement = document.createElement('div');
                scoreElement.className = 'team-score';
                scoreElement.innerHTML = `
                    <h3>Score de l'équipe: ${(team.score * 100).toFixed(1)}/100</h3>
                    <div class="score-breakdown">
                        <div>Couverture des buffs: ${(team.score_breakdown.buff_coverage * 100).toFixed(1)}%</div>
                        <div>Couverture des rôles: ${(team.score_breakdown.role_coverage * 100).toFixed(1)}%</div>
                        <div>Pénalité doublons: -${(team.score_breakdown.duplicate_penalty * 100).toFixed(1)}%</div>
                    </div>
                `;
                teamComposition.prepend(scoreElement);
            } else {
                throw new Error('Aucune équipe générée');
            }
        } catch (error) {
            console.error('Erreur lors de la génération de l\'équipe:', error);
            teamComposition.innerHTML = `
                <div class="error">
                    <p>Erreur lors de la génération de l'équipe :(</p>
                    <p>${error.message}</p>
                    <button onclick="generateTeam()" class="secondary-btn">Réessayer</button>
                </div>
            `;
        }
    }

    // Fonction pour afficher l'équipe générée
    function displayTeam(teamData) {
        const team = teamData.members;
        const teamHTML = `
            <table class="team-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Rôle</th>
                        <th>Classe</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${team.map((member, index) => `
                        <tr>
                            <td>${index + 1}</td>
                            <td>${member.role}</td>
                            <td>${member.profession}</td>
                            <td>
                                ${member.build_url ? 
                                    `<a href="${member.build_url}" target="_blank" class="build-link">Voir le build</a>` : 
                                    '<span class="no-build">Aucun build disponible</span>'
                                }
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            <div class="text-center">
                <button id="regenerateBtn" class="secondary-btn">Générer une nouvelle composition</button>
            </div>
        `;
        
        const teamComposition = document.getElementById('teamComposition');
        teamComposition.innerHTML = teamHTML;
        
        // Ajouter un écouteur d'événements sur le bouton de régénération
        const regenerateBtn = document.getElementById('regenerateBtn');
        if (regenerateBtn) {
            regenerateBtn.addEventListener('click', generateTeam);
        }
    }
});
