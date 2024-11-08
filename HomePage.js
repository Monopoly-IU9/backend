// HomePage.js
import React, { useState } from 'react';
import axios from 'axios';

function HomePage() {
    const [adminData, setAdminData] = useState({
        username: '',
        password: '',
    });
    const [categoryData, setCategoryData] = useState({
        name: '',
        color: '#000000',
    });
    const [setData, setSetData] = useState({
        name: '',
        categoryId: 1,
    });
    const [cardData, setCardData] = useState({
        number: 1,
        description: '',
        hashtags: [],
        setId: 1,
    });
    const [gameData, setGameData] = useState({
        hostId: 1,
    });
    const [qrCode, setQrCode] = useState('');

    const handleAdminRegister = async () => {
        try {
            const response = await axios.post('http://localhost:8000/admin/register', {
                username: adminData.username,
                password: adminData.password,
            });
            alert(response.data.message);
        } catch (error) {
            alert(error.response ? error.response.data.detail : 'Something went wrong');
        }
    };

    const handleCategoryCreate = async () => {
        try {
            const response = await axios.post('http://localhost:8000/category/', categoryData);
            alert(response.data.message);
        } catch (error) {
            alert(error.response ? error.response.data.detail : 'Something went wrong');
        }
    };

    const handleSetCreate = async () => {
        try {
            const response = await axios.post('http://localhost:8000/set/', setData);
            alert(response.data.message);
        } catch (error) {
            alert(error.response ? error.response.data.detail : 'Something went wrong');
        }
    };

    const handleCardCreate = async () => {
        try {
            const response = await axios.post('http://localhost:8000/card/', cardData);
            alert(response.data.message);
        } catch (error) {
            alert(error.response ? error.response.data.detail : 'Something went wrong');
        }
    };

    const handleGameStart = async () => {
        try {
            const response = await axios.post('http://localhost:8000/game/start', gameData);
            alert(response.data.message);
            setQrCode(response.data.game_code);
        } catch (error) {
            alert(error.response ? error.response.data.detail : 'Something went wrong');
        }
    };

    const handleGenerateQrCode = async () => {
        try {
            const response = await axios.get(`http://localhost:8000/game/${qrCode}/qr`);
            alert(response.data.message);
        } catch (error) {
            alert(error.response ? error.response.data.detail : 'Something went wrong');
        }
    };

    return (
        <div>
            <h1>Test Frontend</h1>

            <h2>Admin Register</h2>
            <input
                type="text"
                placeholder="Username"
                value={adminData.username}
                onChange={(e) => setAdminData({ ...adminData, username: e.target.value })}
            />
            <input
                type="password"
                placeholder="Password"
                value={adminData.password}
                onChange={(e) => setAdminData({ ...adminData, password: e.target.value })}
            />
            <button onClick={handleAdminRegister}>Register Admin</button>

            <h2>Create Category</h2>
            <input
                type="text"
                placeholder="Category Name"
                value={categoryData.name}
                onChange={(e) => setCategoryData({ ...categoryData, name: e.target.value })}
            />
            <input
                type="color"
                value={categoryData.color}
                onChange={(e) => setCategoryData({ ...categoryData, color: e.target.value })}
            />
            <button onClick={handleCategoryCreate}>Create Category</button>

            <h2>Create Set</h2>
            <input
                type="text"
                placeholder="Set Name"
                value={setData.name}
                onChange={(e) => setSetData({ ...setData, name: e.target.value })}
            />
            <input
                type="number"
                placeholder="Category ID"
                value={setData.categoryId}
                onChange={(e) => setSetData({ ...setData, categoryId: e.target.value })}
            />
            <button onClick={handleSetCreate}>Create Set</button>

            <h2>Create Card</h2>
            <input
                type="number"
                placeholder="Card Number"
                value={cardData.number}
                onChange={(e) => setCardData({ ...cardData, number: e.target.value })}
            />
            <input
                type="text"
                placeholder="Description"
                value={cardData.description}
                onChange={(e) => setCardData({ ...cardData, description: e.target.value })}
            />
            <input
                type="text"
                placeholder="Hashtags (comma separated)"
                value={cardData.hashtags.join(', ')}
                onChange={(e) => setCardData({ ...cardData, hashtags: e.target.value.split(', ') })}
            />
            <input
                type="number"
                placeholder="Set ID"
                value={cardData.setId}
                onChange={(e) => setCardData({ ...cardData, setId: e.target.value })}
            />
            <button onClick={handleCardCreate}>Create Card</button>

            <h2>Start Game</h2>
            <input
                type="number"
                placeholder="Host ID"
                value={gameData.hostId}
                onChange={(e) => setGameData({ ...gameData, hostId: e.target.value })}
            />
            <button onClick={handleGameStart}>Start Game</button>

            <h2>Generate QR Code</h2>
            <input
                type="text"
                placeholder="Game Code"
                value={qrCode}
                onChange={(e) => setQrCode(e.target.value)}
            />
            <button onClick={handleGenerateQrCode}>Generate QR</button>
        </div>
    );
}

export default HomePage;
