import * as React from 'react';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, Container } from '@mui/material';

export default function SimpleContainer({ children }) {
  return (
    <React.Fragment>
      <CssBaseline />
      <Container maxWidth={false} disableGutters>
        <Box sx={{display: 'flex',
                flexDirection: 'column', 
                bgcolor: '#cfe8fc', 
                height: '100vh', 
                width: '100vw' }}>
            {children}
        </Box>
      </Container>
    </React.Fragment>
  );
}
