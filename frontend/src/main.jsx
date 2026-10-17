import React from 'react';
import {createRoot} from 'react-dom/client';
import '@fontsource/noto-serif-jp/900.css';
import '@fontsource/eb-garamond/400.css';
import '@fontsource/eb-garamond/500.css';
import '@fontsource/eb-garamond/600.css';
import '@fontsource/eb-garamond/400-italic.css';
import '@fontsource/jetbrains-mono/400.css';
import App from './App';
import './styles/index.css';

createRoot(document.getElementById('root')).render(<App/>);
