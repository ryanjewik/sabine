import * as React from 'react';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import '../input-field-style.css';
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from 'axios';

export default function FullWidthTextField() {

  const [inputValue, setInputValue] = useState("");
  const [error, setError] = useState(false);
  const navigate = useNavigate();
  
  const handleKeyPress = async (event) => {
      if (event.key === "Enter") {
          if (inputValue.trim() === "") {
              setError(true);
          } else {
              setError(false);
              try {
                await axios.post('http://localhost:5000/save_input', { input: inputValue });
                navigate("/chatpage");
              } catch (error) {
                console.error('Error saving input:', error);
              }
          }
      }
  };


  return (
    <div className="input-field" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center'}}>
        <Box sx={{ width: '80vw', maxWidth: 1066, margin: 5, padding: 2}} className="text-wrapper">
        <TextField 
            fullWidth label="Ask a question" 
            id="fullWidth"
            variant = "outlined"
            placeholder="Type your question here..." 
            sx={{
                input: { color: '#cfe8fc' },
                label: { color: '#cfe8fc' },
                '& .MuiOutlinedInput-root': {
                  '& fieldset': {
                    borderColor: '#cfe8fc',
                  },
                  '&:hover fieldset': {
                    borderColor: 'green',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: 'green',
                  },
                },
              }}
  
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyPress}
              error={error}
              helperText={error ? 'This field cannot be empty' : ''}
          
        />
        </Box>
    </div>
  );
}
