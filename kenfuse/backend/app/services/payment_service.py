import requests
import base64
import json
from datetime import datetime
from flask import current_app
import stripe
from app.extensions import db
from app.models import Payment, PaymentStatus, PaymentMethod

class MpesaService:
    def __init__(self):
        self.consumer_key = current_app.config['MPESA_CONSUMER_KEY']
        self.consumer_secret = current_app.config['MPESA_CONSUMER_SECRET']
        self.shortcode = current_app.config['MPESA_SHORTCODE']
        self.passkey = current_app.config['MPESA_PASSKEY']
        self.callback_url = current_app.config['MPESA_CALLBACK_URL']
        self.access_token = None
        
    def get_access_token(self):
        """Get M-Pesa access token"""
        url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        auth = base64.b64encode(f"{self.consumer_key}:{self.consumer_secret}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            self.access_token = response.json()['access_token']
            return self.access_token
        except Exception as e:
            current_app.logger.error(f"Error getting M-Pesa token: {str(e)}")
            raise
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """Initiate STK Push payment"""
        if not self.access_token:
            self.get_access_token()
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(
            f"{self.shortcode}{self.passkey}{timestamp}".encode()
        ).decode()
        
        url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            current_app.logger.error(f"Error in STK Push: {str(e)}")
            raise

class StripeService:
    def __init__(self):
        self.secret_key = current_app.config['STRIPE_SECRET_KEY']
        self.publishable_key = current_app.config['STRIPE_PUBLISHABLE_KEY']
        self.webhook_secret = current_app.config['STRIPE_WEBHOOK_SECRET']
        stripe.api_key = self.secret_key
    
    def create_payment_intent(self, amount, currency='kes', metadata=None):
        """Create Stripe payment intent"""
        try:
            # Convert amount to cents/pesas
            amount_in_cents = int(amount * 100)
            
            intent = stripe.PaymentIntent.create(
                amount=amount_in_cents,
                currency=currency,
                metadata=metadata or {},
                payment_method_types=['card'],
            )
            
            return {
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'amount': amount,
                'currency': currency
            }
        except Exception as e:
            current_app.logger.error(f"Error creating payment intent: {str(e)}")
            raise
    
    def handle_webhook(self, payload, sig_header):
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            
            # Handle different event types
            if event['type'] == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                self.handle_successful_payment(payment_intent)
            elif event['type'] == 'payment_intent.payment_failed':
                payment_intent = event['data']['object']
                self.handle_failed_payment(payment_intent)
            
            return True
        except Exception as e:
            current_app.logger.error(f"Error handling webhook: {str(e)}")
            raise
    
    def handle_successful_payment(self, payment_intent):
        """Handle successful payment"""
        # Find and update payment record
        payment = Payment.query.filter_by(
            stripe_payment_intent=payment_intent['id']
        ).first()
        
        if payment:
            payment.status = PaymentStatus.COMPLETED
            payment.transaction_id = payment_intent.get('charges', {}).get('data', [{}])[0].get('id')
            db.session.commit()
    
    def handle_failed_payment(self, payment_intent):
        """Handle failed payment"""
        payment = Payment.query.filter_by(
            stripe_payment_intent=payment_intent['id']
        ).first()
        
        if payment:
            payment.status = PaymentStatus.FAILED
            db.session.commit()

class PaymentService:
    def __init__(self):
        self.mpesa_service = MpesaService()
        self.stripe_service = StripeService()
    
    def create_payment(self, user_id, amount, payment_method, description=None, metadata=None):
        """Create a new payment record"""
        payment = Payment(
            user_id=user_id,
            amount=amount,
            payment_method=payment_method,
            description=description,
            metadata=metadata or {}
        )
        
        db.session.add(payment)
        db.session.commit()
        
        return payment
    
    def process_mpesa_payment(self, user_id, phone_number, amount, description=None):
        """Process M-Pesa payment"""
        try:
            # Create payment record
            payment = self.create_payment(
                user_id=user_id,
                amount=amount,
                payment_method=PaymentMethod.MPESA,
                description=description
            )
            
            # Initiate STK Push
            response = self.mpesa_service.stk_push(
                phone_number=phone_number,
                amount=int(amount),
                account_reference=f"KENFUSE{payment.id[:8]}",
                transaction_desc=description or "KENFUSE Payment"
            )
            
            # Update payment with request data
            if response.get('ResponseCode') == '0':
                payment.metadata = {
                    'checkout_request_id': response.get('CheckoutRequestID'),
                    'merchant_request_id': response.get('MerchantRequestID'),
                    'response_code': response.get('ResponseCode'),
                    'response_description': response.get('ResponseDescription')
                }
                db.session.commit()
                
                return {
                    'success': True,
                    'payment_id': payment.id,
                    'checkout_request_id': response.get('CheckoutRequestID'),
                    'message': 'Payment initiated successfully'
                }
            else:
                payment.status = PaymentStatus.FAILED
                db.session.commit()
                
                return {
                    'success': False,
                    'error': response.get('ResponseDescription', 'Payment failed')
                }
                
        except Exception as e:
            current_app.logger.error(f"Error processing M-Pesa payment: {str(e)}")
            raise
    
    def process_card_payment(self, user_id, amount, description=None, metadata=None):
        """Process card payment"""
        try:
            # Create payment record
            payment = self.create_payment(
                user_id=user_id,
                amount=amount,
                payment_method=PaymentMethod.CARD,
                description=description,
                metadata=metadata
            )
            
            # Create Stripe payment intent
            intent_data = self.stripe_service.create_payment_intent(
                amount=amount,
                currency='kes',
                metadata={
                    'payment_id': payment.id,
                    'user_id': user_id,
                    **(metadata or {})
                }
            )
            
            # Update payment with Stripe intent ID
            payment.stripe_payment_intent = intent_data['payment_intent_id']
            db.session.commit()
            
            return {
                'success': True,
                'payment_id': payment.id,
                'client_secret': intent_data['client_secret'],
                'payment_intent_id': intent_data['payment_intent_id']
            }
            
        except Exception as e:
            current_app.logger.error(f"Error processing card payment: {str(e)}")
            raise
    
    def verify_mpesa_payment(self, checkout_request_id):
        """Verify M-Pesa payment status"""
        # This would typically query M-Pesa API or check callback data
        # For now, we'll simulate verification
        payment = Payment.query.filter_by(
            metadata['checkout_request_id'].astext == checkout_request_id
        ).first()
        
        if payment:
            return {
                'success': True,
                'payment': payment.to_dict()
            }
        
        return {
            'success': False,
            'error': 'Payment not found'
        }