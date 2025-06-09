import React, {useState, useEffect} from 'react'
import Main from './index';
import HomePage from './homepage';
import { Link } from 'react-router-dom';
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Homepage from "./homepage";
import Chatpage from "./chatpage";

function App(){

    const [data, setData] = useState([{}])
    useEffect(() => {
      fetch("/members").then( //we are fetching from the route "/members" which is in the backend flask-server "server.py" file. whatever is returned from the backend will be stored in the data variable using setData
        res => res.json()
      ).then(
        data => {
          setData(data)
          console.log(data)
        }
      )

      /*
        {(typeof data.members ==='undefined') ? (
              <p>Loading...</p>
            ) : (
              data.members.map((member, i) => (
                <p key={i}>{member}</p>
              ))
      )}

      */



      
    }, [])
    return (
      <div>
            <Routes>
              <Route path="/homepage" element={<Homepage />} />
              <Route path="/chatpage" element={<Chatpage />} />
            </Routes>
            
          </div>
    )
}
export default App
