import { Box, Text, VStack, useColorModeValue } from '@chakra-ui/react';
import { useState, useRef, useEffect } from 'react';

import { RoleIcon } from './RoleIcon';

type RoleInfo = {
  description: string;
  responsibilities: string[];
  recommendedProfessions: string[];
};

const ROLE_DESCRIPTIONS: Record<string, RoleInfo> = {
  'DPS': {
    description: 'Responsable des dégâts purs. Se concentre sur l\'élimination rapide des ennemis.',
    responsibilities: [
      'Maximiser les dégâts',
      'Éviter les dégâts inutiles',
      'Suivre les mécaniques de combat'
    ],
    recommendedProfessions: ['Elementalist', 'Thief', 'Ranger']
  },
  'Healer': {
    description: 'Maintient l\'équipe en vie grâce à des soins constants et des buffs de régénération.',
    responsibilities: [
      'Maintenir les soins actifs',
      'Surveiller la vie de l\'équipe',
      'Positionnement stratégique'
    ],
    recommendedProfessions: ['Druid', 'Tempest', 'Firebrand']
  },
  'Tank': {
    description: 'Attire l\'attention des ennemis et absorbe les dégâts pour protéger l\'équipe.',
    responsibilities: [
      'Gérer l\'agro des ennemis',
      'Positionner les boss',
      'Utiliser les compétences défensives au bon moment'
    ],
    recommendedProfessions: ['Chronomancer', 'Firebrand', 'Scrapper']
  },
  'Support': {
    description: 'Fournit des buffs et des bonus essentiels à l\'équipe.',
    responsibilities: [
      'Maintenir les buffs offensifs/défensifs',
      'Aider au contrôle de foule',
      'Soutenir le healer si nécessaire'
    ],
    recommendedProfessions: ['Firebrand', 'Renegade', 'Mech']
  },
  'Boon DPS': {
    description: 'Combine les dégâts avec l\'application de buffs essentiels.',
    responsibilities: [
      'Maintenir les buffs offensifs',
      'Maximiser les dégâts',
      'Coordonner avec les autres rôles de support'
    ],
    recommendedProfessions: ['Herald', 'Mirage', 'Scourge']
  }
};

interface RoleTooltipProps {
  role: string;
  children: React.ReactNode;
}

export const RoleTooltip = ({ role, children }: RoleTooltipProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLSpanElement>(null);
  const roleInfo = ROLE_DESCRIPTIONS[role] || {
    description: 'Rôle non spécifié',
    responsibilities: [],
    recommendedProfessions: []
  };

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  // Gestion des événements clavier
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
      triggerRef.current?.focus();
    }
  };

  // Gestion du clic en dehors
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (tooltipRef.current && !tooltipRef.current.contains(event.target as Node) &&
          triggerRef.current && !triggerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <Box
      as="span"
      ref={triggerRef}
      role="button"
      tabIndex={0}
      aria-haspopup="dialog"
      aria-expanded={isOpen}
      aria-label={`Afficher les détails du rôle ${role}`}
      onKeyDown={(e: React.KeyboardEvent) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          setIsOpen(!isOpen);
        }
      }}
      onClick={(e: React.MouseEvent) => {
        e.preventDefault();
        setIsOpen(!isOpen);
      }}
      sx={{
        display: 'inline-block',
        '&:focus-visible': {
          outline: '2px solid #3182ce',
          outlineOffset: '2px',
          borderRadius: '4px'
        },
        '&:hover .role-tooltip-content, &:focus .role-tooltip-content, &:focus-visible .role-tooltip-content': {
          visibility: isOpen ? 'visible' : 'hidden',
          opacity: isOpen ? 1 : 0,
          transform: isOpen ? 'translateY(0)' : 'translateY(10px)'
        }
      }}
    >
      <Box as="span" position="relative" display="inline-block">
        {children}
        <Box
          ref={tooltipRef}
          className="role-tooltip-content"
          role="dialog"
          aria-labelledby={`${role}-title`}
          position="absolute"
          zIndex="tooltip"
          bg={bgColor}
          color="inherit"
          border="1px solid"
          borderColor={borderColor}
          borderRadius="md"
          p={3}
          w="250px"
          boxShadow="lg"
          visibility={isOpen ? 'visible' : 'hidden'}
          opacity={isOpen ? 1 : 0}
          transform={isOpen ? 'translateY(0)' : 'translateY(10px)'}
          transition="all 0.2s ease-in-out"
          left="50%"
          transformOrigin="top center"
          onKeyDown={handleKeyDown}
          _before={{
            content: '""',
            position: 'absolute',
            bottom: '100%',
            left: '50%',
            marginLeft: '-8px',
            borderWidth: '8px',
            borderStyle: 'solid',
            borderColor: `transparent transparent ${borderColor} transparent`,
          }}
          _after={{
            content: '""',
            position: 'absolute',
            bottom: '100%',
            left: '50%',
            marginLeft: '-6px',
            borderWidth: '6px',
            borderStyle: 'solid',
            borderColor: 'transparent',
            borderBottomColor: bgColor,
            marginBottom: '-1px',
          }}
        >
          <VStack align="start" spacing={2}>
            <Box display="flex" alignItems="center" id={`${role}-title`}>
              <RoleIcon role={role} boxSize={5} mr={2} aria-hidden="true" />
              <Text as="h3" fontWeight="bold" fontSize="lg" m={0}>{role}</Text>
            </Box>
            
            <Text fontSize="sm">{roleInfo.description}</Text>
            
            {roleInfo.responsibilities.length > 0 && (
              <Box width="100%">
                <Text fontWeight="bold" fontSize="sm" mb={1}>Responsabilités :</Text>
                <VStack align="start" spacing={1} pl={2}>
                  {roleInfo.responsibilities.map((item, i) => (
                    <Text key={i} fontSize="xs" display="flex" alignItems="flex-start">
                      <Box as="span" mr={2}>•</Box>
                      {item}
                    </Text>
                  ))}
                </VStack>
              </Box>
            )}
            
            {roleInfo.recommendedProfessions.length > 0 && (
              <Box width="100%" pt={1}>
                <Text fontWeight="bold" fontSize="sm" mb={1}>Professions recommandées :</Text>
                <Box display="flex" flexWrap="wrap" gap={1}>
                  {roleInfo.recommendedProfessions.map((profession, i) => (
                    <Box
                      key={i}
                      bg={useColorModeValue('gray.100', 'gray.700')}
                      px={2}
                      py={0.5}
                      borderRadius="md"
                      fontSize="xs"
                      aria-label={profession}
                    >
                      <span aria-hidden="true">{profession}</span>
                    </Box>
                  ))}
                </Box>
              </Box>
            )}
          </VStack>
        </Box>
      </Box>
    </Box>
  );
};
