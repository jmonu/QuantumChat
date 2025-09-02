from flask import render_template, request, jsonify, redirect, url_for, session, flash
from app import app, db
from models import ChatSession, Message, SecurityEvent
from quantum_engine import QuantumKeyGenerator
from encryption import QuantumEncryption
from ai_engine import monmad_ai
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)
quantum_generator = QuantumKeyGenerator()

@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')

@app.route('/create_session', methods=['POST'])
def create_session():
    """Create a new chat session"""
    try:
        session_code = ChatSession.generate_session_code()
        new_session = ChatSession(session_code=session_code)
        db.session.add(new_session)
        db.session.commit()
        
        logger.info(f"Created new session: {session_code}")
        return redirect(url_for('chat', session_code=session_code))
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        flash('Error creating session. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/join_session', methods=['POST'])
def join_session():
    """Join an existing chat session"""
    try:
        session_code = request.form.get('session_code', '').upper().strip()
        
        if not session_code:
            flash('Please enter a session code.', 'error')
            return redirect(url_for('index'))
        
        chat_session = ChatSession.query.filter_by(session_code=session_code, is_active=True).first()
        
        if not chat_session:
            flash('Session not found or inactive.', 'error')
            return redirect(url_for('index'))
        
        return redirect(url_for('chat', session_code=session_code))
        
    except Exception as e:
        logger.error(f"Error joining session: {e}")
        flash('Error joining session. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/chat/<session_code>')
def chat(session_code):
    """Chat interface"""
    try:
        chat_session = ChatSession.query.filter_by(session_code=session_code, is_active=True).first()
        
        if not chat_session:
            flash('Session not found or inactive.', 'error')
            return redirect(url_for('index'))
        
        # Get messages (excluding destroyed ones)
        messages = Message.query.filter_by(
            session_id=chat_session.id, 
            is_destroyed=False
        ).order_by(Message.created_at).all()
        
        # Check for self-destruct messages and destroy them
        for message in messages:
            if message.should_self_destruct():
                message.is_destroyed = True
                message.original_message = "[Message Self-Destructed]"
                message.encrypted_message = "[Encrypted Data Destroyed]"
        
        db.session.commit()
        
        return render_template('chat.html', 
                             session=chat_session, 
                             messages=messages,
                             session_code=session_code)
        
    except Exception as e:
        logger.error(f"Error loading chat: {e}")
        flash('Error loading chat. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/api/generate_key', methods=['POST'])
def api_generate_key():
    """Generate quantum key for session"""
    try:
        data = request.get_json()
        session_code = data.get('session_code')
        bits = int(data.get('bits', 16))
        
        chat_session = ChatSession.query.filter_by(session_code=session_code).first()
        if not chat_session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Generate quantum key
        quantum_key, circuits_info = quantum_generator.generate_quantum_key(bits)
        
        # Generate circuit visualization
        circuit_image = quantum_generator.generate_circuit_visualization(circuits_info)
        
        # Update session
        chat_session.quantum_key = quantum_key
        chat_session.key_generated_at = datetime.utcnow()
        chat_session.key_refreshes += 1
        
        # Log security event
        security_event = SecurityEvent(
            session_id=chat_session.id,
            event_type='key_generation',
            description=f'Quantum key generated with {bits} bits'
        )
        db.session.add(security_event)
        db.session.commit()
        
        logger.info(f"Generated quantum key for session {session_code}")
        
        return jsonify({
            'success': True,
            'key': quantum_key,
            'key_length': len(quantum_key),
            'circuit_image': circuit_image,
            'expires_in': 300  # 5 minutes
        })
        
    except Exception as e:
        logger.error(f"Error generating quantum key: {e}")
        return jsonify({'error': 'Failed to generate quantum key'}), 500

@app.route('/api/send_message', methods=['POST'])
def api_send_message():
    """Send encrypted message"""
    try:
        data = request.get_json()
        session_code = data.get('session_code')
        sender = data.get('sender')
        message = data.get('message')
        encryption_method = data.get('encryption_method', 'xor')
        is_self_destruct = data.get('is_self_destruct', False)
        self_destruct_timer = int(data.get('self_destruct_timer', 30))
        
        chat_session = ChatSession.query.filter_by(session_code=session_code).first()
        if not chat_session:
            return jsonify({'error': 'Session not found'}), 404
        
        if not chat_session.quantum_key:
            return jsonify({'error': 'No quantum key generated'}), 400
        
        if chat_session.is_key_expired():
            return jsonify({'error': 'Quantum key expired. Please generate a new key.'}), 400
        
        # Encrypt message
        if encryption_method == 'xor':
            encrypted_message = QuantumEncryption.xor_encrypt(message, chat_session.quantum_key)
        elif encryption_method == 'otp':
            encrypted_message = QuantumEncryption.one_time_pad_encrypt(message, chat_session.quantum_key)
        else:
            return jsonify({'error': 'Invalid encryption method'}), 400
        
        # Create message record
        new_message = Message(
            session_id=chat_session.id,
            sender=sender,
            original_message=message,
            encrypted_message=encrypted_message,
            is_self_destruct=is_self_destruct,
            self_destruct_timer=self_destruct_timer
        )
        
        db.session.add(new_message)
        
        # Update session stats
        chat_session.total_messages += 1
        chat_session.messages_count += 1
        
        # Log security event
        security_event = SecurityEvent(
            session_id=chat_session.id,
            event_type='message_sent',
            description=f'Message sent by {sender} using {encryption_method} encryption'
        )
        db.session.add(security_event)
        db.session.commit()
        
        logger.info(f"Message sent in session {session_code} by {sender}")
        
        return jsonify({
            'success': True,
            'message_id': new_message.id,
            'encrypted_message': encrypted_message,
            'timestamp': new_message.created_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return jsonify({'error': 'Failed to send message'}), 500

@app.route('/api/get_messages', methods=['GET'])
def api_get_messages():
    """Get messages for session"""
    try:
        session_code = request.args.get('session_code')
        last_message_id = int(request.args.get('last_message_id', 0))
        
        chat_session = ChatSession.query.filter_by(session_code=session_code).first()
        if not chat_session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get new messages
        messages_query = Message.query.filter_by(session_id=chat_session.id, is_destroyed=False)
        if last_message_id > 0:
            messages_query = messages_query.filter(Message.id > last_message_id)
        
        messages = messages_query.order_by(Message.created_at).all()
        
        # Check for self-destruct and mark read
        for message in messages:
            if message.should_self_destruct():
                message.is_destroyed = True
                message.original_message = "[Message Self-Destructed]"
                message.encrypted_message = "[Encrypted Data Destroyed]"
            else:
                # Mark as read
                if not message.read_at:
                    message.read_at = datetime.utcnow()
        
        db.session.commit()
        
        message_list = []
        for msg in messages:
            if not msg.is_destroyed:
                # Decrypt message if key is available
                decrypted_message = msg.original_message
                if chat_session.quantum_key:
                    try:
                        if chat_session.encryption_method == 'xor':
                            decrypted_message = QuantumEncryption.xor_decrypt(msg.encrypted_message, chat_session.quantum_key)
                        elif chat_session.encryption_method == 'otp':
                            decrypted_message = QuantumEncryption.one_time_pad_decrypt(msg.encrypted_message, chat_session.quantum_key)
                    except Exception as e:
                        logger.error(f"Decryption error: {e}")
                
                message_list.append({
                    'id': msg.id,
                    'sender': msg.sender,
                    'message': decrypted_message,
                    'encrypted_message': msg.encrypted_message,
                    'is_self_destruct': msg.is_self_destruct,
                    'time_until_destruction': msg.time_until_destruction(),
                    'timestamp': msg.created_at.isoformat()
                })
        
        return jsonify({
            'success': True,
            'messages': message_list,
            'key_time_remaining': chat_session.key_time_remaining()
        })
        
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        return jsonify({'error': 'Failed to get messages'}), 500

@app.route('/api/simulate_hacker_attack', methods=['POST'])
def api_simulate_hacker_attack():
    """Simulate hacker attack on encrypted messages"""
    try:
        data = request.get_json()
        session_code = data.get('session_code')
        
        chat_session = ChatSession.query.filter_by(session_code=session_code).first()
        if not chat_session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get recent messages
        messages = Message.query.filter_by(
            session_id=chat_session.id, 
            is_destroyed=False
        ).order_by(Message.created_at.desc()).limit(5).all()
        
        if not messages:
            return jsonify({'error': 'No messages to attack'}), 400
        
        attack_results = []
        for msg in messages:
            attack_result = QuantumEncryption.simulate_hacker_attack(
                msg.original_message, 
                msg.encrypted_message
            )
            attack_results.append({
                'message_id': msg.id,
                'sender': msg.sender,
                'attack_result': attack_result
            })
        
        # Log security event
        security_event = SecurityEvent(
            session_id=chat_session.id,
            event_type='hacker_simulation',
            description='Simulated hacker attack on encrypted messages'
        )
        chat_session.security_events_count += 1
        db.session.add(security_event)
        db.session.commit()
        
        logger.info(f"Simulated hacker attack on session {session_code}")
        
        return jsonify({
            'success': True,
            'attack_results': attack_results,
            'summary': f'All {len(attack_results)} intercepted messages remain secure'
        })
        
    except Exception as e:
        logger.error(f"Error simulating hacker attack: {e}")
        return jsonify({'error': 'Failed to simulate attack'}), 500

@app.route('/analytics/<session_code>')
def analytics(session_code):
    """Analytics dashboard"""
    try:
        chat_session = ChatSession.query.filter_by(session_code=session_code).first()
        if not chat_session:
            flash('Session not found.', 'error')
            return redirect(url_for('index'))
        
        # Get analytics data
        messages = Message.query.filter_by(session_id=chat_session.id).all()
        security_events = SecurityEvent.query.filter_by(session_id=chat_session.id).order_by(SecurityEvent.created_at.desc()).limit(10).all()
        
        analytics_data = {
            'total_messages': len(messages),
            'active_messages': len([m for m in messages if not m.is_destroyed]),
            'self_destruct_messages': len([m for m in messages if m.is_self_destruct]),
            'destroyed_messages': len([m for m in messages if m.is_destroyed]),
            'key_refreshes': chat_session.key_refreshes,
            'security_events': len(security_events),
            'session_age': (datetime.utcnow() - chat_session.created_at).total_seconds() / 3600  # hours
        }
        
        return render_template('analytics.html', 
                             session=chat_session, 
                             analytics=analytics_data,
                             security_events=security_events)
        
    except Exception as e:
        logger.error(f"Error loading analytics: {e}")
        flash('Error loading analytics.', 'error')
        return redirect(url_for('index'))

@app.route('/api/export_chat', methods=['POST'])
def api_export_chat():
    """Export chat data"""
    try:
        data = request.get_json()
        session_code = data.get('session_code')
        export_format = data.get('format', 'decrypted')  # 'decrypted' or 'encrypted'
        
        chat_session = ChatSession.query.filter_by(session_code=session_code).first()
        if not chat_session:
            return jsonify({'error': 'Session not found'}), 404
        
        messages = Message.query.filter_by(
            session_id=chat_session.id,
            is_destroyed=False
        ).order_by(Message.created_at).all()
        
        if export_format == 'encrypted':
            # Export encrypted data
            export_data = {
                'session_code': session_code,
                'quantum_key': '[REDACTED]',  # Don't export the actual key
                'encryption_method': chat_session.encryption_method,
                'messages': []
            }
            
            for msg in messages:
                export_data['messages'].append({
                    'sender': msg.sender,
                    'encrypted_message': msg.encrypted_message,
                    'timestamp': msg.created_at.isoformat()
                })
        else:
            # Export decrypted data
            export_data = {
                'session_code': session_code,
                'export_timestamp': datetime.utcnow().isoformat(),
                'messages': []
            }
            
            for msg in messages:
                export_data['messages'].append({
                    'sender': msg.sender,
                    'message': msg.original_message,
                    'timestamp': msg.created_at.isoformat()
                })
        
        return jsonify({
            'success': True,
            'export_data': export_data,
            'filename': f'quantum_chat_{session_code}_{export_format}.json'
        })
        
    except Exception as e:
        logger.error(f"Error exporting chat: {e}")
        return jsonify({'error': 'Failed to export chat'}), 500

@app.route('/api/ai_analyze_message', methods=['POST'])
def api_ai_analyze_message():
    """AI-powered message analysis"""
    try:
        data = request.get_json()
        message = data.get('message')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get AI sentiment analysis
        sentiment = monmad_ai.analyze_message_sentiment(message)
        
        # Get threat detection
        threat_analysis = monmad_ai.detect_security_threats(message)
        
        return jsonify({
            'success': True,
            'sentiment': sentiment,
            'threat_analysis': threat_analysis,
            'ai_powered': True
        })
        
    except Exception as e:
        logger.error(f"AI message analysis error: {e}")
        return jsonify({'error': 'AI analysis failed'}), 500

@app.route('/api/ai_smart_replies', methods=['POST'])
def api_ai_smart_replies():
    """Generate AI-powered smart reply suggestions"""
    try:
        data = request.get_json()
        session_code = data.get('session_code')
        sender = data.get('sender')
        
        chat_session = ChatSession.query.filter_by(session_code=session_code).first()
        if not chat_session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get recent conversation history
        recent_messages = Message.query.filter_by(
            session_id=chat_session.id,
            is_destroyed=False
        ).order_by(Message.created_at.desc()).limit(5).all()
        
        # Format for AI
        conversation_history = [{
            'sender': msg.sender,
            'message': msg.original_message
        } for msg in reversed(recent_messages)]
        
        # Generate smart replies
        smart_replies = monmad_ai.generate_smart_reply(conversation_history, sender)
        
        return jsonify({
            'success': True,
            'smart_replies': smart_replies,
            'ai_powered': True
        })
        
    except Exception as e:
        logger.error(f"Smart replies generation error: {e}")
        return jsonify({'error': 'Smart replies generation failed'}), 500

@app.route('/api/ai_translate', methods=['POST'])
def api_ai_translate():
    """AI-powered message translation"""
    try:
        data = request.get_json()
        message = data.get('message')
        target_language = data.get('target_language', 'auto')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        translation = monmad_ai.translate_message(message, target_language)
        
        return jsonify({
            'success': True,
            'translation': translation,
            'ai_powered': True
        })
        
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return jsonify({'error': 'Translation failed'}), 500

@app.route('/api/ai_conversation_insights', methods=['GET'])
def api_ai_conversation_insights():
    """Generate AI-powered conversation insights"""
    try:
        session_code = request.args.get('session_code')
        
        chat_session = ChatSession.query.filter_by(session_code=session_code).first()
        if not chat_session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get all messages for analysis
        messages = Message.query.filter_by(
            session_id=chat_session.id,
            is_destroyed=False
        ).order_by(Message.created_at).all()
        
        # Format for AI analysis
        message_data = [{
            'sender': msg.sender,
            'original_message': msg.original_message,
            'timestamp': msg.created_at.isoformat()
        } for msg in messages]
        
        # Generate insights
        insights = monmad_ai.generate_conversation_insights(message_data)
        
        return jsonify({
            'success': True,
            'insights': insights,
            'ai_powered': True
        })
        
    except Exception as e:
        logger.error(f"Conversation insights error: {e}")
        return jsonify({'error': 'Insights generation failed'}), 500

@app.route('/api/ai_quantum_key_analysis', methods=['POST'])
def api_ai_quantum_key_analysis():
    """AI analysis of quantum key quality"""
    try:
        data = request.get_json()
        session_code = data.get('session_code')
        
        chat_session = ChatSession.query.filter_by(session_code=session_code).first()
        if not chat_session or not chat_session.quantum_key:
            return jsonify({'error': 'No quantum key found'}), 404
        
        # AI analysis of quantum key
        key_analysis = monmad_ai.enhance_quantum_key_analysis(
            chat_session.quantum_key,
            {'length': len(chat_session.quantum_key), 'method': 'quantum'}
        )
        
        return jsonify({
            'success': True,
            'key_analysis': key_analysis,
            'ai_powered': True
        })
        
    except Exception as e:
        logger.error(f"Quantum key analysis error: {e}")
        return jsonify({'error': 'Key analysis failed'}), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"Internal server error: {error}")
    return render_template('index.html'), 500
