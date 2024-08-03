// src/RealTimeHandGesture.js
import React, { useEffect, useRef, useState } from 'react';
import io from 'socket.io-client';

const socket = io('http://127.0.0.1:5000');

function HandGesture() {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const [result, setResult] = useState(null);

    useEffect(() => {
        socket.on('result', (data) => {
            setResult(data);
        });

        return () => {
            socket.off('result');
        };
    }, []);

    useEffect(() => {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        const context = canvas.getContext('2d');

        const startVideo = () => {
            navigator.mediaDevices.getUserMedia({ video: true })
                .then((stream) => {
                    video.srcObject = stream;
                    video.play();
                })
                .catch((err) => console.error('Error accessing webcam:', err));
        };

        const captureFrame = () => {
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            const imageData = canvas.toDataURL('image/jpeg');
            socket.emit('image', imageData);
        };

        video.addEventListener('playing', () => {
            setInterval(captureFrame, 100); // Capture frame every 100ms
        });

        startVideo();
    }, []);

    return (
        <div>
            <h1>Real-Time Hand Gesture Detection</h1>
            <video ref={videoRef} width="500" height="320" style={{ display: 'block',transform: 'scaleX(-1)' }}></video>
            <canvas ref={canvasRef} width="640" height="480" style={{ display: 'none' }}></canvas>
            {result && (
                <div>
                    <h2>Detection Result</h2>
                    <pre>{JSON.stringify(result, null, 2)}</pre>
                </div>
            )}
        </div>
    );
}

export default HandGesture;
