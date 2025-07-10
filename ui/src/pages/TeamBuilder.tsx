import { 
  Box, Button, FormControl, FormLabel, NumberInput, NumberInputField, 
  Select, VStack, useToast, Heading, Text, SimpleGrid, Badge 
} from '@chakra-ui/react';
import { useState } from 'react';

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
    teams: Array<TeamResult>;
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
        description: `Génération de ${data.teams?.length || 0} compositions réussie !`,
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
            Configuration de l'équipe
          </Heading>
          <Box color="gray.600" fontSize="sm">
            L&apos;algorithme génétique va calculer la meilleure composition possible
          </Box>
        </Box>

        <FormControl isRequired>
          <FormLabel>Taille de l'équipe</FormLabel>
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
          <FormLabel>Style de jeu</FormLabel>
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
            <Box as="strong" display="block" mb={1}>Algorithme génétique actif</Box>
            <Box fontSize="xs" opacity={0.8} mb={2}>
              {config.defaults.generations} générations × {config.defaults.population} combinaisons testées
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
                  L'algorithme génétique crée des équipes optimales en simulant l'évolution naturelle :
                </Text>
                <VStack align="stretch" spacing={1}>
                  <Box display="flex" alignItems="flex-start">
                    <Box as="span" fontWeight="bold" minW="24" color="blue.600">1. Population initiale</Box>
                    <Box>Création de {config.defaults.population} équipes aléatoires</Box>
                  </Box>
                  <Box display="flex" alignItems="flex-start">
                    <Box as="span" fontWeight="bold" minW="24" color="blue.600">2. Évaluation</Box>
                    <Box>Chaque équipe est notée sur sa couverture des rôles et des buffs</Box>
                  </Box>
                  <Box display="flex" alignItems="flex-start">
                    <Box as="span" fontWeight="bold" minW="24" color="blue.600">3. Sélection</Box>
                    <Box>Les meilleures équipes sont sélectionnées pour se reproduire</Box>
                  </Box>
                  <Box display="flex" alignItems="flex-start">
                    <Box as="span" fontWeight="bold" minW="24" color="blue.600">4. Croisement</Box>
                    <Box>Les équipes sélectionnées se combinent pour créer de nouvelles équipes</Box>
                  </Box>
                  <Box display="flex" alignItems="flex-start">
                    <Box as="span" fontWeight="bold" minW="24" color="blue.600">5. Mutation</Box>
                    <Box>Des changements aléatoires introduisent de la diversité</Box>
                  </Box>
                  <Box display="flex" alignItems="flex-start">
                    <Box as="span" fontWeight="bold" minW="24" color="blue.600">6. Itération</Box>
                    <Box>Le processus se répète sur {config.defaults.generations} générations</Box>
                  </Box>
                </VStack>
                <Text mt={2} fontSize="xs" fontStyle="italic">
                  Ce processus permet de trouver un bon équilibre entre exploration et optimisation.
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
              {results.teams.length} composition(s) générée(s) pour une équipe de {results.request.team_size} joueurs en mode {results.request.playstyle}
            </Text>

            <SimpleGrid columns={{ base: 1, md: Math.min(3, results.teams.length) }} spacing={6} mt={6}>
              {results.teams.map((team, index) => (
                <Box 
                  key={index} 
                  borderWidth="1px" 
                  borderRadius="lg" 
                  p={4}
                  bg="white"
                  boxShadow="sm"
                >
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                    <Text fontWeight="bold" fontSize="lg">
                      Composition #{index + 1}
                    </Text>
                    <Badge colorScheme={team.score > 0.7 ? 'green' : team.score > 0.4 ? 'yellow' : 'red'}>
                      Score: {(team.score * 100).toFixed(0)}%
                    </Badge>
                  </Box>
                  
                  <VStack align="stretch" spacing={2} mt={2}>
                    {team.members.map((member, i) => (
                      <Box 
                        key={i} 
                        p={2} 
                        bg="gray.50" 
                        borderRadius="md"
                        borderLeft="3px solid"
                        borderLeftColor="blue.300"
                      >
                        <Text fontWeight="medium">{member.profession}</Text>
                        <Text fontSize="sm" color="gray.600">{member.role}</Text>
                      </Box>
                    ))}
                  </VStack>
                  
                  <Box mt={3} fontSize="xs" color="gray.500">
                    <Text>Couverture des buffs: {(team.score_breakdown.buff_coverage * 100).toFixed(0)}%</Text>
                    <Text>Couverture des rôles: {(team.score_breakdown.role_coverage * 100).toFixed(0)}%</Text>
                    {team.score_breakdown.duplicate_penalty > 0 && (
                      <Text>Pénalité doublons: -{(team.score_breakdown.duplicate_penalty * 100).toFixed(0)}%</Text>
                    )}
                  </Box>
                </Box>
              ))}
            </SimpleGrid>
          </Box>
        )}
      </VStack>
    </Box>
  );
};

export default TeamBuilder;
