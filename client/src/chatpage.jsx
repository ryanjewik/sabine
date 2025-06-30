import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from 'react-markdown';
import { Link, useLocation } from "react-router-dom";
import "./chatpagestyle.css";
import { ReactComponent as UserPFP } from "./img/user-profile-pic.svg";
import { ReactComponent as ViperPFP } from "./img/viper-profile-pic.svg";
import axios from 'axios';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';



export const ChatPage = () => {
  const location = useLocation();
  const [userId, setUserId] = useState(location.state?.userId || null);
  const initialInput = location.state?.input || "";
  const [messages, setMessages] = useState(initialInput ? [
    { sender: "user", text: initialInput, timestamp: new Date().toLocaleString('en-US') }
  ] : []);
  const [input, setInput] = useState("");
  const [convoId, setConvoId] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [loginOpen, setLoginOpen] = useState(false);
  const [signupOpen, setSignupOpen] = useState(false);
  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [signupUsername, setSignupUsername] = useState("");
  const [signupPassword, setSignupPassword] = useState("");
  const chatEndRef = useRef(null);

  // Log userId on mount to confirm receipt
  useEffect(() => {
    console.log('ChatPage loaded with userId:', userId);
  }, [userId]);


  // Fetch messages from backend on mount
  const fetchMessages = async () => {
    try {
      const res = await axios.post('http://localhost:5000/get_messages', { userId: userId });
      if (res.data && res.data.messages) {
        setMessages(prev => initialInput ? [
          { sender: "user", text: initialInput, timestamp: new Date().toLocaleString('en-US') },
          ...res.data.messages
        ] : res.data.messages);
      }
      if (res.data.convoId) {
        setConvoId(res.data.convoId);
        console.log('Conversation ID:', res.data.convoId);
      }
    } catch (err) {
      console.error('Failed to fetch messages:', err);
    }
  };

  useEffect(() => {
    if (userId !== -1){
      fetchMessages();
    }else{
      if (initialInput) {
        setMessages([{ sender: "user", text: initialInput, timestamp: new Date().toLocaleString('en-US') }]);
      }
      console.log('No userId provided, skipping message fetch');
    }
  }, [userId]);

  // Fetch conversations for sidebar
  const fetchConversations = async () => {
    if (userId && userId !== -1) {
      try {
        const res = await axios.post('http://localhost:5000/get_conversations', { userId });
        if (res.data && res.data.conversations) {
          setConversations(res.data.conversations);
        }
      } catch (err) {
        const res = await axios.post('http://localhost:5000/new_conversation', { userId: userId });
        setConvoId(res.data.conversationId);
        fetchConversations(); // Refresh conversations after creating new chat
        fetchMessages(); // Fetch messages for the new conversation
        console.error('Failed to fetch conversations:', err);
      }
    }
  };

  useEffect(() => {
    fetchConversations();
  }, [userId]);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  //handle sending a message
  const handleSend = async (event) => {
    if (event) event.preventDefault();
    if (!input.trim()) return;
    const date = new Date();
    try {
      let isFirstMessage = messages.length === 0;
      let response;
      if (userId !== -1) {
        response = await axios.post('http://localhost:5000/save_input', { input: input, sender: "user", userId: userId, conversationId: convoId, timestamp: date.toLocaleString('en-US') });
        setConvoId(response.data.convoId);
        // If this is the first message, rename the conversation
        if (isFirstMessage && convoId) {
          await axios.post('http://localhost:5000/rename_conversation', { userId: userId, conversationId: convoId, title: input });
          fetchConversations();
        }
      }
      setMessages([...messages, { sender: "user", text: input, timestamp: date.toLocaleString('en-US') }, {sender: "bot", text: response.data.chatbot_response, timestamp: date.toLocaleString('en-US') }]);
      setInput("");
    } catch (error) {
      console.error("Error sending message:", error);
    }
  };
  //handle new conversation

    const handleNewChat = async () => {
    try {
      const res = await axios.post('http://localhost:5000/new_conversation', { userId: userId });
      setConvoId(res.data.conversationId);
      fetchConversations(); // Refresh conversations after creating new chat
      setMessages([]); // Clear messages for new chat
      console.log('New chat created with conversation ID:', res.data.conversationId);
    } catch (err) {
      console.error('Failed to create new chat:', err);
    }
    };

  // Handle input change and log it for debugging
  const handleInputChange = (event) => {
    setInput(event.target.value);
    console.log('Input changed:', event.target.value); // Debug: input change
  };

  const handleInputKeyDown = (event) => {
    if (event.key === 'Enter') {
      handleSend(event);
    }
  };

  const handleSelectConversation = async (conversationId) => {
    setConvoId(conversationId);
    try {
      const res = await axios.post('http://localhost:5000/get_messages', { userId: userId, conversationId: conversationId });
      if (res.data && res.data.messages) {
        setMessages(res.data.messages);
      }
    } catch (err) {
      console.error('Failed to fetch messages for conversation:', err);
    }
  };

  const handleLoginOpen = () => { setLoginOpen(true); setSignupOpen(false); };
  const handleLoginClose = () => setLoginOpen(false);
  const handleSignupOpen = () => { setSignupOpen(true); setLoginOpen(false); };
  const handleSignupClose = () => setSignupOpen(false);

  const handleLoginSubmit = async(event) => {
    if (event) event.preventDefault();
    try {
      // Call backend to login
      const response = await axios.post('http://localhost:5000/login', {
        username: loginUsername,
        password: loginPassword
      });
      if (response.status === 200 && response.data.userId) {
        const placeholder = response.data.userId;
        setUserId(placeholder); // Update userId from response
        setLoginOpen(false);
        // If there is a chat in progress (messages), add it as a conversation for this user
        if (messages && messages.length > 0) {
          // Create new conversation for user
          const convoRes = await axios.post('http://localhost:5000/new_conversation', {
            userId: response.data.userId,
            name: messages[0].text // Use first message as conversation name
          });
          const newConvoId = convoRes.data.conversationId;
          // Add all messages to this conversation
          for (const msg of messages) {
            await axios.post('http://localhost:5000/save_input', {
              input: msg.text,
              sender: msg.sender,
              userId: response.data.userId,
              conversationId: newConvoId,
              timestamp: msg.timestamp || new Date().toLocaleString('en-US')
            });
          }
          setConvoId(newConvoId);
          fetchConversations();
          setLoginOpen(false);
        }
      }
    } catch (error) {
      console.error('Error logging in:', error);
    }
  };

    const handleSignUpSubmit = async(event) => {
        console.log("Sign Up submitted with username:", signupUsername, "and password:", signupPassword);
        if (event) event.preventDefault();
        // TODO: Add signup logic here
        //postgres database connection and signup logic
        //ensure there are no duplicates
        
        const error = validateSignup(signupUsername, signupPassword);
        if (error) {
            alert(error); // Or set an error state to display in the UI
            return;
        }
        try {
            const response = await axios.post('http://localhost:5000/signup', { username: signupUsername, password: signupPassword });
            if (response.status === 201) {
                const userId = response.data.userId
                console.log('User signed up:', signupUsername);
                setSignupOpen(false);
            }
        } catch (error) {
            console.error('Error signing up:', error);
            alert(error.response.data.error);
        }
        
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
    <div className="chat-gpt-layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <span>Chats</span>
        </div>
        <div className="sidebar-chats">
          {userId === -1 && (
            <div className="sidebar-auth-buttons" style={{ display: 'flex', flexDirection: 'column'}}>
              <button className="new-chat-btn" onClick={handleLoginOpen}>Login</button>
              <button className="new-chat-btn" onClick={handleSignupOpen}>Sign Up</button>
            </div>
          )}
          <button className="new-chat-btn" onClick={handleNewChat}>New Chat</button>
          {conversations.length > 0 ? (
            conversations.map((conv, idx) => (
              <div className={`sidebar-chat-item${convoId === conv.conversationId ? ' active' : ''}`} key={conv.conversationId || idx} onClick={() => handleSelectConversation(conv.conversationId)}>
                <span>{conv.name || conv.title || `Conversation ${idx + 1}`}</span>
              </div>
            ))
          ) : (
            <div className="sidebar-chat-item">
              <span>No conversations yet</span>
            </div>
          )}
        </div>
      </aside>
      <main className="chat-main">
        <div className="chat-messages">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`chat-message ${msg.sender === "user" ? "user" : "bot"}`}
            >
              {msg.sender === "bot" ? (
                <ViperPFP className="chat-avatar" />
              ) : (
                <UserPFP className="chat-avatar" />
              )}
              <div className="chat-bubble">
                <div className="chat-text">
                  {msg.sender === "bot" ? (
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  ) : (
                    msg.text
                  )}
                </div>
                <div className="chat-time">{msg.time}</div>
              </div>
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>
        <div className="chat-input-bar">
          <input
            className="chat-input"
            type="text"
            placeholder="Type your message..."
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleInputKeyDown}
            autoFocus
          />
          <button className="send-btn" type="button" onClick={handleSend}>Send</button>
        </div>
      </main>
      {/* Login Dialog */}
      <Dialog open={loginOpen} onClose={handleLoginClose}>
        <DialogTitle className="custom-dialog-title" sx={{fontFamily: 'Anonymous Pro-Regular, monospace'}}>Login</DialogTitle>
        <DialogContent className="dialog-element">
          <form onSubmit={handleLoginSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16, minWidth: 300 }}>
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
      {/* Signup Dialog */}
      <Dialog open={signupOpen} onClose={handleSignupClose}>
        <DialogTitle className="custom-dialog-title" sx={{fontFamily: 'Anonymous Pro-Regular, monospace'}}>Sign Up</DialogTitle>
        <DialogContent className="dialog-element">
          <form onSubmit={handleSignUpSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16, minWidth: 300 }}>
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
    </div>
  );
};

export default ChatPage;
