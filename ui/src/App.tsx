import { ChakraProvider, Box, Heading, Container } from '@chakra-ui/react';

import TeamBuilder from './pages/TeamBuilder';

function App() {
  return (
    <ChakraProvider>
      <Box minH="100vh" bg="gray.50">
        <Container maxW="container.lg" py={8}>
          <Heading as="h1" size="xl" mb={8} textAlign="center" color="blue.600">
            Guild Wars 2 Team Builder
          </Heading>
          <TeamBuilder />
        </Container>
      </Box>
    </ChakraProvider>
  );
}

export default App;
