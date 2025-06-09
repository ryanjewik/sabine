import * as React from 'react';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import '../input-field-style.css';

export default function FullWidthTextField() {
  return (
    <div className="input-field" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center'}}>
        <Box sx={{ width: '80vw', maxWidth: 1066, margin: 5, padding: 2}} className="text-wrapper">
        <TextField 
            fullWidth label="Ask a question" 
            id="fullWidth"
            variant = "outlined"
            placeholder="Type your question here..." 
            sx={{
                input: { color: 'white' },
                label: { color: 'white' },
                '& .MuiOutlinedInput-root': {
                  '& fieldset': {
                    borderColor: 'white',
                  },
                  '&:hover fieldset': {
                    borderColor: 'green',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: 'green',
                  },
                },
              }}
        />
        </Box>
    </div>
  );
}
