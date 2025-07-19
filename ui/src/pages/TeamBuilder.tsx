// Dependencies
import {
  Box, Button, FormControl, FormLabel, NumberInput, NumberInputField,
  Select, VStack, useToast, Heading, Text, SimpleGrid
} from '@chakra-ui/react';
import { useState } from 'react';

import { InfoTooltip } from '../components/InfoTooltip';
import config from '../config';

interface TeamMember {
  role: string;
  profession: string;
  build_url: string;
}

interface TeamResult {
  members: TeamMember[];
  score: number;
  score_breakdown: {
    buff_coverage: number;
    role_coverage: number;
    duplicate_penalty: number;
    total: number;
  };
}

const TeamBuilder = () => {
  const [formData, setFormData] = useState({
    team_size: config.defaults.teamSize,
    playstyle: config.defaults.playstyle,
  });
  
  const [results, setResults] = useState<{
    team: TeamResult;
    request: {
      team_size: number;
      playstyle: string;
    };
    metadata: Record<string, unknown>;
  } | null>(null);
  
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();

  const handleInputChange = (field: string, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setResults(null);
    
    try {
      const requestData = {
        team_size: formData.team_size,
        playstyle: formData.playstyle,
      };

      const response = await fetch(`${config.api.baseUrl}${config.api.endpoints.teams.generate}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Erreur lors de la génération de l\'équipe');
      }

      const data = await response.json();
      setResults(data);
      
      toast({
        title: 'Succès',
        description: 'Composition d\'équipe générée avec succès !',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
    } catch (error: unknown) {
      console.error('Erreur:', error);
      toast({
        title: 'Erreur',
        description: error instanceof Error ? error.message : 'Une erreur est survenue lors de la génération de l\'équipe.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box as="form" onSubmit={handleSubmit} bg="white" p={6} rounded="lg" shadow="md">
      <VStack spacing={6} align="stretch">
        <Box textAlign="center" mb={6}>
          <Heading as="h2" size="lg" color="blue.600" mb={2}>
            Configuration de l&apos;équipe
          </Heading>
          <Box color="gray.600" fontSize="sm">
            L&apos;optimiseur va calculer la meilleure composition possible
          </Box>
        </Box>

        <FormControl isRequired>
          <FormLabel>
            Taille de l&apos;&eacute;quipe
            <InfoTooltip 
              label="Nombre de joueurs dans l&apos;&eacute;quipe (1-10)"
              iconProps={{
                'aria-label': 'Information sur la taille de l&apos;&eacute;quipe'
              }}
            />
          </FormLabel>
          <NumberInput 
            min={1}
            max={10}
            value={formData.team_size}
            onChange={(_, value) => handleInputChange('team_size', value || 1)}
          >
            <NumberInputField />
          </NumberInput>
        </FormControl>

        <FormControl isRequired>
          <FormLabel>
            Style de jeu
            <InfoTooltip 
              label="S&eacute;lectionnez le type de contenu pour lequel optimiser l&apos;&eacute;quipe"
              iconProps={{
                'aria-label': 'Information sur le style de jeu'
              }}
            />
          </FormLabel>
          <Select 
            value={formData.playstyle}
            onChange={(e) => handleInputChange('playstyle', e.target.value)}
            placeholder="Sélectionnez un style de jeu"
          >
            {config.playstyles.map((style) => (
              <option key={style.value} value={style.value}>
                {style.label}
              </option>
            ))}
          </Select>
        </FormControl>

        <Box mt={4} p={4} bg="blue.50" borderRadius="md" borderLeft="4px" borderColor="blue.500">
          <Box fontSize="sm" color="blue.800">
            <Box as="strong" display="block" mb={1}>Méthode d&apos;optimisation</Box>
            <Box fontSize="xs" opacity={0.8} mb={2}>
              {config.defaults.samples} combinaisons testées pour trouver la meilleure équipe
            </Box>
            <Box 
              as="details" 
              cursor="pointer" 
              fontSize="xs" 
              opacity={0.8}
              _hover={{ opacity: 1 }}
              sx={{ '&[open]': { opacity: 1 } }}
            >
              <summary style={{ cursor: 'pointer', outline: 'none' }}>Comment ça marche ?</summary>
              <Box mt={2} p={2} bg="white" borderRadius="md" fontSize="xs">
                <Text mb={2}>
                  L&apos;optimiseur évalue {config.defaults.samples} combinaisons aléatoires pour trouver la meilleure équipe :
                </Text>
                <VStack align="stretch" spacing={1}>
                  <Box display="flex" alignItems="flex-start">
                    <Box as="span" fontWeight="bold" minW="24" color="blue.600">1. Échantillonnage</Box>
                    <Box>Création de {config.defaults.samples} équipes aléatoires</Box>
                  </Box>
                  <Box display="flex" alignItems="flex-start">
                    <Box as="span" fontWeight="bold" minW="24" color="blue.600">2. Évaluation</Box>
                    <Box>Chaque équipe est notée sur sa couverture des rôles et des buffs</Box>
                  </Box>
                  <Box display="flex" alignItems="flex-start">
                    <Box as="span" fontWeight="bold" minW="24" color="blue.600">3. Sélection</Box>
                    <Box>Les meilleures équipes sont sélectionnées et retournées</Box>
                  </Box>
                </VStack>
                <Text mt={2} fontSize="xs" fontStyle="italic">
                  Cette méthode simple et efficace permet de trouver rapidement une bonne composition d&apos;équipe.
                </Text>
              </Box>
            </Box>
          </Box>
        </Box>

        <Button 
          type="submit" 
          colorScheme="blue" 
          size="lg" 
          width="100%"
          isLoading={isLoading}
          loadingText="Génération en cours..."
          mt={4}
        >
          Générer l&apos;équipe
        </Button>

        {results && (
          <Box mt={8}>
            <Heading size="md" mb={4} color="blue.700">
              Résultats de la génération
            </Heading>
            
            <Text fontSize="sm" color="gray.600" mb={4}>
              Composition générée pour une équipe de {results.request.team_size} joueurs en mode {results.request.playstyle}
            </Text>

            <Box borderWidth="1px" borderRadius="lg" p={4} bg="white" boxShadow="sm">
              <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4} mt={2}>
                {results.team.members.map((member, index) => (
                  <Box 
                    key={index} 
                    borderWidth="1px" 
                    borderRadius="md" 
                    p={3}
                    bg="white"
                    _hover={{ shadow: 'md' }}
                  >
                    <Box display="flex" alignItems="center" mb={2}>
                      <Text fontWeight="bold" fontSize="lg">{member.profession}</Text>
                    </Box>
                    <Box>
                      <Text fontSize="sm" color="gray.600" mb={1}>
                        Rôle: {member.role}
                      </Text>
                      {member.build_url && member.build_url !== '#' && (
                        <Button 
                          as="a" 
                          href={member.build_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          size="sm"
                          colorScheme="blue"
                          variant="outline"
                          mt={2}
                        >
                          Voir le build
                        </Button>
                      )}
                    </Box>
                  </Box>
                ))}
              </SimpleGrid>
              
              <Box mt={4} p={3} bg="gray.50" borderRadius="md">
                <Text fontWeight="bold" mb={2}>Détails du score:</Text>
                <Text>Couverture des buffs: {(results.team.score_breakdown.buff_coverage * 100).toFixed(1)}%</Text>
                <Text>Couverture des rôles: {(results.team.score_breakdown.role_coverage * 100).toFixed(1)}%</Text>
                <Text>Pénalité doublons: {results.team.score_breakdown.duplicate_penalty > 0 ? `-${(results.team.score_breakdown.duplicate_penalty * 100).toFixed(1)}%` : 'Aucune'}</Text>
              </Box>
            </Box>
          </Box>
        )}
      </VStack>
    </Box>
  );
};

export default TeamBuilder;
