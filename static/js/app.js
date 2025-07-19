// Fonction pour afficher l'équipe générée
function displayTeam(teamData) {
    const team = teamData.members;
    const teamHTML = `
        <div class="team-header">
            <h2>Équipe Optimisée</h2>
            <div class="team-score">
                <strong>Score :</strong> ${(teamData.score * 100).toFixed(1)}/100
                <div class="score-breakdown">
                    <span class="badge">Buffs: ${(teamData.score_breakdown.buff_coverage * 100).toFixed(0)}%</span>
                    <span class="badge">Rôles: ${(teamData.score_breakdown.role_coverage * 100).toFixed(0)}%</span>
                    ${teamData.score_breakdown.duplicate_penalty ? 
                        `<span class="badge warning">Doublons: -${(teamData.score_breakdown.duplicate_penalty * 100).toFixed(0)}%</span>` : ''}
                </div>
            </div>
        </div>
        <table class="team-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Rôle</th>
                    <th>Classe</th>
                    <th>Spécialisation</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${team.map((member, index) => `
                    <tr>
                        <td>${index + 1}</td>
                        <td><span class="role-badge ${member.role.toLowerCase()}">${member.role}</span></td>
                        <td>
                            <div class="profession">
                                <img src="/static/img/professions/${member.profession.toLowerCase()}.png" 
                                     alt="${member.profession}" 
                                     class="profession-icon"
                                     onerror="this.style.display='none'"
                                >
                                ${member.profession}
                            </div>
                        </td>
                        <td>${member.specialization || 'Standard'}</td>
                        <td>
                            ${member.build_url ? 
                                `<a href="${member.build_url}" target="_blank" class="build-link">
                                    <i class="fas fa-external-link-alt"></i> Voir le build
                                </a>` : 
                                '<span class="no-build">Détails non disponibles</span>'
                            }
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
        <div class="team-actions">
            <button id="regenerateBtn" class="primary-btn">
                <i class="fas fa-sync-alt"></i> Régénérer l'équipe
            </button>
            <button id="exportBtn" class="secondary-btn">
                <i class="fas fa-download"></i> Exporter l'équipe
            </button>
        </div>
    `;
    
    const teamComposition = document.getElementById('teamComposition');
    if (teamComposition) {
        teamComposition.innerHTML = teamHTML;
        
        // Ajouter les écouteurs d'événements
        const regenerateBtn = document.getElementById('regenerateBtn');
        if (regenerateBtn) {
            regenerateBtn.addEventListener('click', generateTeam);
        }
        
        const exportBtn = document.getElementById('exportBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                alert('Fonctionnalité d\'export à implémenter');
            });
        }
    }
}

// Fonction pour générer une équipe
async function generateTeam() {
    const teamSize = parseInt(document.getElementById('teamSize').value);
    const playstyle = document.getElementById('playstyle').value;
    
    // Afficher un indicateur de chargement
    const teamComposition = document.getElementById('teamComposition');
    teamComposition.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Génération de l'équipe optimale en cours...</p>
            <p class="loading-details">Analyse des synergies et optimisation des rôles</p>
        </div>`;
    
    try {
        // Appel à l'API pour générer une équipe
        const response = await fetch('/api/teams/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                team_size: teamSize,
                playstyle: playstyle,
                // Ajout de paramètres pour des builds plus détaillés
                include_build_details: true,
                optimize_for: 'synergy' // Peut être 'synergy', 'damage', 'support', etc.
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Erreur HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Vérifier que nous avons bien une équipe dans la réponse
        if (data.team) {
            // Afficher l'équipe générée
            displayTeam(data.team);
            
            // Faire défiler jusqu'à la section des résultats
            document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
        } else {
            throw new Error('Format de réponse inattendu de l\'API');
        }
    } catch (error) {
        console.error('Erreur lors de la génération de l\'équipe:', error);
        teamComposition.innerHTML = `
            <div class="error">
                <div class="error-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <h3>Erreur lors de la génération de l'équipe</h3>
                <p>${error.message || 'Une erreur inattendue est survenue'}</p>
                <div class="error-actions">
                    <button id="retryBtn" class="primary-btn">
                        <i class="fas fa-redo"></i> Réessayer
                    </button>
                    <button id="reportBtn" class="secondary-btn">
                        <i class="fas fa-bug"></i> Signaler un problème
                    </button>
                </div>
            </div>`;
        
        // Ajouter les écouteurs d'événements pour les boutons d'erreur
        const retryBtn = document.getElementById('retryBtn');
        if (retryBtn) {
            retryBtn.addEventListener('click', generateTeam);
        }
        
        const reportBtn = document.getElementById('reportBtn');
        if (reportBtn) {
            reportBtn.addEventListener('click', () => {
                console.error('Rapport d\'erreur:', {
                    error: error.toString(),
                    timestamp: new Date().toISOString(),
                    teamSize: document.getElementById('teamSize')?.value,
                    playstyle: document.getElementById('playstyle')?.value
                });
                alert('Merci de signaler ce problème. Les détails ont été enregistrés dans la console.');
            });
        }
    }
}

// Initialisation au chargement du document
document.addEventListener('DOMContentLoaded', () => {
    // S'assurer que la fonction est disponible dans la portée globale
    window.generateTeam = generateTeam;
    
    // Ajouter l'écouteur d'événement pour le bouton de génération
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        generateBtn.addEventListener('click', generateTeam);
    } else {
        console.error('Bouton de génération non trouvé');
    }
});
