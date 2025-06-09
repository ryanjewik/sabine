import * as React from 'react';
import Box from '@mui/material/Box';
import CssBaseline from '@mui/material/CssBaseline';

export default function BoxBasic({ children }) {
  return (
    <React.Fragment>
        <CssBaseline />
            <Box sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        height: '100vh',
                        width: '100vw',
                        position: 'absolute',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        color: '#333333'
                    }}>
                {children}
            </Box>
    </React.Fragment>
  );
}
