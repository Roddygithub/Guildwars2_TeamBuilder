import { Box, Text, VStack, useColorModeValue } from '@chakra-ui/react';
import { useState, useRef, useEffect, KeyboardEvent } from 'react';

interface ScoreBreakdown {
  buff_coverage: number;
  role_coverage: number;
  duplicate_penalty: number;
  total: number;
}

interface ScoreTooltipProps {
  score: number;
  breakdown: ScoreBreakdown;
  children: React.ReactNode;
}

export const ScoreTooltip = ({ score, breakdown, children }: ScoreTooltipProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLSpanElement>(null);
  const firstFocusableRef = useRef<HTMLButtonElement>(null);
  const lastFocusableRef = useRef<HTMLDivElement>(null);

  // Gestion des événements clavier
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
      triggerRef.current?.focus();
    } else if (e.key === 'Tab' && isOpen) {
      // Piège de focus
      if (e.shiftKey && document.activeElement === firstFocusableRef.current) {
        e.preventDefault();
        lastFocusableRef.current?.focus();
      } else if (!e.shiftKey && document.activeElement === lastFocusableRef.current) {
        e.preventDefault();
        firstFocusableRef.current?.focus();
      }
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

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      // Mettre le focus sur le premier élément focusable
      setTimeout(() => firstFocusableRef.current?.focus(), 100);
    }

    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  // Animation d'apparition
  const fadeIn = `
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `;
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const goodScoreColor = useColorModeValue('green.500', 'green.300');
  const mediumScoreColor = useColorModeValue('yellow.500', 'yellow.300');
  const badScoreColor = useColorModeValue('red.500', 'red.300');

  const getScoreColor = (value: number) => {
    if (value >= 0.7) return goodScoreColor;
    if (value >= 0.4) return mediumScoreColor;
    return badScoreColor;
  };

  const formatPercentage = (value: number) => {
    return `${Math.round(value * 100)}%`;
  };

  const getScoreFeedback = (value: number) => {
    if (value >= 0.8) return 'Excellent';
    if (value >= 0.6) return 'Bon';
    if (value >= 0.4) return 'Moyen';
    return 'À améliorer';
  };

  return (
    <Box
      as="span"
      ref={triggerRef}
      position="relative"
      display="inline-flex"
      role="button"
      tabIndex={0}
      aria-haspopup="dialog"
      aria-expanded={isOpen}
      aria-label="Afficher les détails du score"
      onKeyDown={(e: KeyboardEvent) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          setIsOpen(!isOpen);
        } else if (e.key === 'Escape' && isOpen) {
          e.preventDefault();
          setIsOpen(false);
        }
      }}
      onClick={(e: React.MouseEvent) => {
        e.preventDefault();
        setIsOpen(!isOpen);
      }}
      sx={{
        cursor: 'pointer',
        '&:focus-visible': {
          outline: '2px solid #3182ce',
          outlineOffset: '2px',
          borderRadius: '4px',
        },
        '&:hover .score-tooltip-content, &:focus .score-tooltip-content, &:focus-visible .score-tooltip-content': {
          visibility: isOpen ? 'visible' : 'hidden',
          opacity: isOpen ? 1 : 0,
          transform: isOpen ? 'translateY(0)' : 'translateY(10px)'
        }
      }}
    >
      <Box as="span">
        {children}
      </Box>
      
      <Box
        ref={tooltipRef}
        className="score-tooltip-content"
        role="dialog"
        aria-labelledby="score-details-title"
        position="absolute"
        zIndex="tooltip"
        bg={bgColor}
        color="inherit"
        border="1px solid"
        borderColor={borderColor}
        borderRadius="md"
        p={4}
        w="280px"
        boxShadow="lg"
        visibility={isOpen ? 'visible' : 'hidden'}
        opacity={isOpen ? 1 : 0}
        transform={isOpen ? 'translateY(0)' : 'translateY(10px)'}
        transition="all 0.2s ease-in-out"
        left="50%"
        transformOrigin="top center"
        css={fadeIn}
        animation="fadeIn 0.2s ease-out"
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
        <VStack align="stretch" spacing={3}>
          <Box>
            <Text id="score-details-title" fontWeight="bold" fontSize="lg" mb={1}>
              Détail du score
            </Text>
            <button 
              ref={firstFocusableRef}
              onClick={(e: React.MouseEvent) => {
                e.stopPropagation();
                setIsOpen(false);
                triggerRef.current?.focus();
              }}
              style={{
                position: 'absolute',
                top: '0.5rem',
                right: '0.5rem',
                background: 'none',
                border: 'none',
                fontSize: '1.2rem',
                cursor: 'pointer',
                padding: '0.25rem',
                borderRadius: '4px',
              }}
              aria-label="Fermer"
            >
              ×
            </button>
            <Text 
              id="score-summary" 
              fontSize="sm" 
              color="gray.600"
              tabIndex={0}
              aria-live="polite"
              aria-atomic="true"
            >
              {getScoreFeedback(score)} - {formatPercentage(score)}
            </Text>
          </Box>

          <VStack align="stretch" spacing={2}>
            <Box>
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Text fontSize="sm">Couverture des buffs</Text>
                <Text fontSize="sm" fontWeight="medium" color={getScoreColor(breakdown.buff_coverage)}>
                  {formatPercentage(breakdown.buff_coverage)}
                </Text>
              </Box>
              <Box h="4px" bg="gray.200" borderRadius="full" overflow="hidden">
                <Box 
                  h="100%" 
                  bg={getScoreColor(breakdown.buff_coverage)}
                  width={`${breakdown.buff_coverage * 100}%`}
                />
              </Box>
            </Box>

            <Box>
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Text fontSize="sm">Couverture des rôles</Text>
                <Text fontSize="sm" fontWeight="medium" color={getScoreColor(breakdown.role_coverage)}>
                  {formatPercentage(breakdown.role_coverage)}
                </Text>
              </Box>
              <Box h="4px" bg="gray.200" borderRadius="full" overflow="hidden">
                <Box 
                  h="100%" 
                  bg={getScoreColor(breakdown.role_coverage)}
                  width={`${breakdown.role_coverage * 100}%`}
                />
              </Box>
            </Box>

            <Box>
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Text fontSize="sm">Pénalité de doublons</Text>
                <Text 
                  fontSize="sm" 
                  fontWeight="medium" 
                  color={badScoreColor}
                  aria-label={`Pénalité de doublons: ${formatPercentage(breakdown.duplicate_penalty)}`}
                >
                  -{formatPercentage(breakdown.duplicate_penalty)}
                </Text>
              </Box>
              <Box h="4px" bg="gray.200" borderRadius="full" overflow="hidden">
                <Box 
                  h="100%" 
                  bg={badScoreColor}
                  width={`${breakdown.duplicate_penalty * 100}%`}
                />
              </Box>
            </Box>
          </VStack>

          <Box pt={2} borderTopWidth="1px" borderTopColor={borderColor}>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Text fontSize="sm" fontWeight="bold">Score total</Text>
              <Box as="div" tabIndex={0} ref={lastFocusableRef}>
                <Text 
                  fontSize="lg" 
                  fontWeight="bold" 
                  color={getScoreColor(breakdown.total)}
                  aria-label={`Score total: ${formatPercentage(breakdown.total)}`}
                >
                  {formatPercentage(breakdown.total)}
                </Text>
              </Box>
            </Box>
          </Box>
        </VStack>
      </Box>
    </Box>
  );
};
