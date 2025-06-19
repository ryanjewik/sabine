import * as React from 'react';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, Container } from '@mui/material';
import Fade from '@mui/material/Fade';

export default function SimpleContainer({ children }) {
  const [loaded, setLoaded] = React.useState(false);
  React.useEffect(() => {
    const timer = setTimeout(() => setLoaded(true), 100); // slight delay
    return () => clearTimeout(timer);
  }, []);

  return (
    <React.Fragment>
      <CssBaseline />
      <Container maxWidth={false} disableGutters ={true} sx={{ height: '100vh', width: '100vw', overflow: 'hidden', bgcolor: 'black' }}>
        <Fade in={true} easing= {{ enter: 'ease-out', exit: 'ease-in' }} timeout={1000}>
          {/* Using Box to create a full-width and full-height container */}
          <Box sx={{display: 'flex',
                  flexDirection: 'column', 
                  bgcolor: loaded ? '#cfe8fc' : 'black',
                  transition: 'background-color 1000ms ease-in-out',
                  height: '100vh', 
                  width: '100vw' }}>
              {children}
          </Box>
        </Fade>
      </Container>
    </React.Fragment>
  );
}
