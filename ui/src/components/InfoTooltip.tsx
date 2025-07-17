import { Tooltip, Icon, IconProps } from '@chakra-ui/react';
import { FaInfoCircle } from 'react-icons/fa';

type InfoTooltipProps = {
  label: string;
  iconProps?: IconProps;
};

export const InfoTooltip = ({ label, iconProps }: InfoTooltipProps) => {
  return (
    <Tooltip 
      label={label} 
      aria-label="Information"
      placement="top"
      hasArrow
      bg="gray.700"
      color="white"
      p={3}
      borderRadius="md"
      maxW="300px"
    >
      <span>
        <Icon 
          as={FaInfoCircle} 
          color="blue.500" 
          ml={1} 
          boxSize={4} 
          display="inline-flex"
          verticalAlign="middle"
          cursor="help"
          {...iconProps}
        />
      </span>
    </Tooltip>
  );
};
