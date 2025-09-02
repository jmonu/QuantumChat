# Quantum Secure Chat App

## Overview

The Quantum Secure Chat App is a real-time two-user chat system that demonstrates quantum cryptography concepts through a Flask web application. The system allows two users (Alice and Bob) to communicate using quantum-generated encryption keys, with features like self-destructing messages, security analytics, and hacker view visualization. The app uses Qiskit for quantum key generation and implements XOR encryption to secure messages.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
The frontend uses a modern web stack with Bootstrap 5 for responsive UI components and a WhatsApp-style dark/light theme system. The chat interface features separate input controls for Alice and Bob, real-time message display with encryption visualization, and a "hacker view" toggle to show intercepted ciphertext. JavaScript classes handle client-side functionality including message polling, key timer management, theme switching, and analytics visualization using Chart.js.

### Backend Architecture
Built on Flask with SQLAlchemy ORM using a declarative base model. The application follows a modular structure with separate files for routes, models, encryption logic, and quantum engine functionality. Session management uses server-side database storage with unique 8-character session codes. The backend provides RESTful API endpoints for session management, message encryption/decryption, quantum key generation, and analytics data.

### Database Schema
Uses SQLAlchemy with support for both SQLite (development) and PostgreSQL (production) through environment variable configuration. Key models include:
- ChatSession: Stores session codes, quantum keys, encryption methods, and analytics counters
- Message: Contains both original and encrypted message content with self-destruct capabilities
- SecurityEvent: Tracks security-related activities and anomalies

The database includes automatic table creation on application startup and proper foreign key relationships between sessions and messages.

### Encryption System
Implements XOR encryption with quantum-generated keys as the primary encryption method. The encryption module provides symmetric encrypt/decrypt functions with error handling that gracefully falls back to plaintext on encryption failures. Keys expire after 5 minutes to maintain security, and the system supports future extension to other encryption methods like one-time pad.

### Quantum Key Generation
Uses Qiskit library to generate truly quantum keys through quantum circuit simulation. The system creates superposition states using Hadamard gates and measures qubits to generate random bits. Each key generation process stores circuit information for visualization and educational purposes, demonstrating the quantum nature of the key generation process.

## External Dependencies

### Quantum Computing
- **Qiskit**: IBM's quantum computing framework for generating quantum keys through circuit simulation
- **Matplotlib**: Used for quantum circuit visualization with non-interactive backend for server deployment

### Web Framework
- **Flask**: Core web framework with SQLAlchemy integration for database operations
- **Flask-SQLAlchemy**: Database ORM with connection pooling and migration support

### Frontend Libraries
- **Bootstrap 5**: Responsive UI framework for modern interface components
- **Font Awesome**: Icon library for consistent visual elements
- **Chart.js**: JavaScript charting library for analytics visualization

### Database Support
- **SQLite**: Default development database with file-based storage
- **PostgreSQL**: Production database support through DATABASE_URL environment variable
- **SQLAlchemy**: Database abstraction layer with connection pooling

### Development Tools
- **Python Logging**: Comprehensive logging system for debugging and monitoring
- **Secrets Module**: Cryptographically secure random number generation for session codes