import React from 'react';
import './homepagestyle.css';
import { Link } from "react-router-dom";
import SimpleContainer from "./components/simplecontainer";

export const HomePage = () => {
    return (
        <SimpleContainer>
            <div className="home-page">
                <h1 className="title">Welcome to ChatGPT</h1>
                <p className="subtitle">Your AI-powered chat assistant</p>
                <Link to="/chatpage" className="chat-link">Go to Chat Page</Link>
            </div>
        </SimpleContainer>
    );
}

export default HomePage;