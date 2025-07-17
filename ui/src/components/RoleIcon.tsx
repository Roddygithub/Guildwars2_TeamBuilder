import { Icon, IconProps } from '@chakra-ui/react';
import { FaUser, FaShieldAlt, FaHeart, FaMagic, FaCrosshairs, FaFistRaised } from 'react-icons/fa';

type RoleIconProps = IconProps & {
  role: string;
};

const roleIcons: Record<string, React.ElementType> = {
  // Rôles principaux
  'DPS': FaFistRaised,
  'Healer': FaHeart,
  'Tank': FaShieldAlt,
  'Support': FaMagic,
  'Boon DPS': FaCrosshairs,
  
  // Classes
  'Guardian': FaShieldAlt,
  'Warrior': FaFistRaised,
  'Engineer': FaCrosshairs,
  'Ranger': FaCrosshairs,
  'Thief': FaCrosshairs,
  'Elementalist': FaMagic,
  'Mesmer': FaMagic,
  'Necromancer': FaMagic,
  'Revenant': FaShieldAlt,
};

export const RoleIcon = ({ role, ...props }: RoleIconProps) => {
  const IconComponent = roleIcons[role] || FaUser;
  
  // Couleurs par rôle
  const colorMap: Record<string, string> = {
    'DPS': 'red.500',
    'Healer': 'green.500',
    'Tank': 'blue.500',
    'Support': 'purple.500',
    'Boon DPS': 'orange.500',
  };

  return (
    <Icon 
      as={IconComponent} 
      color={colorMap[role] || 'gray.500'} 
      boxSize={5} 
      mr={2}
      title={role}
      {...props}
    />
  );
};
