import React from 'react';
import './homepagestyle.css';
import { Link } from "react-router-dom";
import BoxBasic from "./components/box";
import SimpleContainer from "./components/simplecontainer";
import Box from '@mui/material/Box';
import FullWidthTextField from './components/textfield';

export const HomePage = () => {
    return (
        <SimpleContainer>
            <div className="home-page" style={{ display: 'grid', gridTemplateRows: '1fr 1fr', height: '100vh', backgroundImage: 'radial-gradient(circle,rgba(0, 255, 0, 0.63), #003300)' }}>
                <BoxBasic
                    sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#333333'
                    }}
                >
                    <h1 className="title">Welcome to Sabine</h1>
                    <p className="subtitle">Your AI-powered chat assistant</p>
                    <FullWidthTextField placeholder="Ask a question" />
                    
                    <Link to="/chatpage" className="chat-link">Go to Chat Page</Link>
                </BoxBasic>
            </div>
        </SimpleContainer>
    );
}

export default HomePage;