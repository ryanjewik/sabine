import React, { useEffect, useRef, useState } from 'react';
import './homepagestyle.css';
import { Link } from "react-router-dom";
import BoxBasic from "./components/box";
import SimpleContainer from "./components/simplecontainer";
import FullWidthTextField from './components/textfield';
import Grow from '@mui/material/Grow';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import axios from 'axios';

export const HomePage = () => {
    const chatEndRef = useRef(null);
    const [loginOpen, setLoginOpen] = useState(false);
    const [signupOpen, setSignupOpen] = useState(false);
    const [loginUsername, setLoginUsername] = useState("");
    const [loginPassword, setLoginPassword] = useState("");
    const [signupUsername, setSignupUsername] = useState("");
    const [signupPassword, setSignupPassword] = useState("");
    const [isLoggedIn, setIsLoggedIn] = useState(false);

    const handleLoginOpen = () => { setLoginOpen(true); setSignupOpen(false); };
    const handleLoginClose = () => setLoginOpen(false);
    const handleSignupOpen = () => { setSignupOpen(true); setLoginOpen(false); };
    const handleSignupClose = () => setSignupOpen(false);


    const handleLoginSubmit = async(event) => {
        event.preventDefault();
        try {
            const response = await axios.post('http://localhost:5000/login', {
                username: loginUsername,
                password: loginPassword
            });
            if (response.data.success) {
                setIsLoggedIn(true);
                setLoginOpen(false);
            } else {
                alert(response.data.message);
            }
        } catch (error) {
            console.error('Error logging in:', error);
        }
    };

    const handleSignUpSubmit = async(event) => {
        event.preventDefault();
        // TODO: Add signup logic here
        //postgres database connection and signup logic
        //ensure there are no duplicates
        
        const error = validateSignup(signupUsername, signupPassword);
        if (error) {
            alert(error); // Or set an error state to display in the UI
            return;
        }
        try {
            await axios.post('http://localhost:5000/signup', { username: signupUsername, password: signupPassword });
            console.log('User signed up:', signupUsername);
            

        } catch (error) {
            console.error('Error signing up:', error);
            const confirmation = false;
        }
        const confirmation = true;
        // what do I do with this data now?
        //automatically signin
        setIsLoggedIn(true);
        setSignupOpen(false);
    };


    //password validation function
    const validateSignup = (username, password) => {
    // Username: not empty (add more rules if needed)
    if (!username.trim()) return "Username cannot be empty.";

    // Password: at least 8 chars, 1 uppercase, 1 number, 1 special char
    if (password.length < 8) return "Password must be at least 8 characters.";
    if (!/[A-Z]/.test(password)) return "Password must have at least one uppercase letter.";
    if (!/[0-9]/.test(password)) return "Password must have at least one number.";
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) return "Password must have at least one special character.";

    return null; // No errors
    };



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
                    {/*main elements */}
                    <Grow in={true} timeout={1000}><h1 className="title">Welcome to Sabine</h1></Grow>
                    <Grow in={true} timeout={1500}><p className="subtitle">Your AI-powered chat assistant</p></Grow>
                    <FullWidthTextField placeholder="Ask a question" />

                    {/*extra buttons for login and signup */}
                    {!isLoggedIn && (
                        <div className="button-container">
                            <Grow in={true} timeout={2000}>
                                <Link to="#" className="login-button" onClick={e => { e.preventDefault(); handleLoginOpen(); }}>Login</Link>
                            </Grow>
                            <Grow in={true} timeout={2000}>
                                <Link to="#" className="login-button" onClick={e => { e.preventDefault(); handleSignupOpen(); }}>Sign Up</Link>
                            </Grow>
                        </div>
                    )}

                    <Link to="/chatpage" className="chat-link">Go to Chat Page</Link>
                </BoxBasic>
                <div ref={chatEndRef} />
            </div>

            {/* Login Dialog */}
            <Dialog open={loginOpen} onClose={handleLoginClose}>
                <DialogTitle className="custom-dialog-title" sx= {{fontFamily: 'Anonymous Pro-Regular, monospace'}}>Login</DialogTitle>
                <DialogContent className="dialog-element">
                    <form onSubmit={e => { e.preventDefault(); setLoginOpen(false); }} style={{ display: 'flex', flexDirection: 'column', gap: 16, minWidth: 300}}>
                        <TextField 
                            label="Username" 
                            value={loginUsername} 
                            onChange={e => setLoginUsername(e.target.value)} 
                            fullWidth 
                            margin="dense"
                            sx={{
                                input: { color: 'white' },
                                label: { color: 'white' },
                                '& .MuiOutlinedInput-root': {
                                    '& fieldset': {
                                        borderColor: 'white',
                                    },
                                    '&:hover fieldset': {
                                        borderColor: 'white',
                                    },
                                    '&.Mui-focused fieldset': {
                                        borderColor: 'white',
                                    },
                                },
                            }}
                        />
                        <TextField 
                            label="Password" 
                            type="password" 
                            value={loginPassword} 
                            onChange={e => setLoginPassword(e.target.value)} 
                            fullWidth 
                            margin="dense"
                            sx={{
                                input: { color: 'white' },
                                label: { color: 'white' },
                                '& .MuiOutlinedInput-root': {
                                    '& fieldset': {
                                        borderColor: 'white',
                                    },
                                    '&:hover fieldset': {
                                        borderColor: 'white',
                                    },
                                    '&.Mui-focused fieldset': {
                                        borderColor: 'white',
                                    },
                                },
                            }}
                        />
                        <Link to="#" className="login-button" 
                            style={{marginTop: 0, fontSize: 16, color: "#FF4655"}} 
                            onClick={e => { e.preventDefault(); handleSignupOpen(); }}>Sign Up
                        </Link>
                        <Button variant="contained" color="primary" type="submit" style={{marginTop: 16}}>Login</Button>
                    </form>
                </DialogContent>
            </Dialog>

            {/* Sign Up Dialog */}
            <Dialog open={signupOpen} onClose={handleSignupClose}>
                <DialogTitle className="custom-dialog-title" sx= {{fontFamily: 'Anonymous Pro-Regular, monospace'}}>Sign Up</DialogTitle>
                <DialogContent className="dialog-element">
                    <form onSubmit={e => { e.preventDefault(); setSignupOpen(false); }} style={{ display: 'flex', flexDirection: 'column', gap: 16, minWidth: 300 }}>
                        <TextField 
                            label="Username" 
                            value={signupUsername} 
                            onChange={e => setSignupUsername(e.target.value)} 
                            fullWidth 
                            margin="dense"
                            sx={{
                                input: { color: 'white' },
                                label: { color: 'white' },
                                '& .MuiOutlinedInput-root': {
                                    '& fieldset': {
                                        borderColor: 'white',
                                    },
                                    '&:hover fieldset': {
                                        borderColor: 'white',
                                    },
                                    '&.Mui-focused fieldset': {
                                        borderColor: 'white',
                                    },
                                },
                            }}
                        />
                        <TextField 
                            label="Password" 
                            type="password" 
                            value={signupPassword} 
                            onChange={e => setSignupPassword(e.target.value)} 
                            fullWidth 
                            margin="dense"
                            sx={{
                                input: { color: 'white' },
                                label: { color: 'white' },
                                '& .MuiOutlinedInput-root': {
                                    '& fieldset': {
                                        borderColor: 'white',
                                    },
                                    '&:hover fieldset': {
                                        borderColor: 'white',
                                    },
                                    '&.Mui-focused fieldset': {
                                        borderColor: 'white',
                                    },
                                },
                            }}
                        />
                        <Link to="#" className="login-button" 
                            style={{marginTop: 0, fontSize: 16, color: "#FF4655"}} 
                            onClick={e => { e.preventDefault(); handleLoginOpen(); }}>Login
                        </Link>
                        <Button variant="contained" color="primary" type="submit" style={{marginTop: 16}}>Sign Up</Button>
                    </form>
                </DialogContent>
            </Dialog>
        </SimpleContainer>
    );
}

export default HomePage;