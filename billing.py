import stripe

stripe.api_key = os.environ["STRIPE_SECRET_KEY_TEST"]
stripe_public_key = os.environ["STRIPE_PUBLIC_KEY_TEST"]
