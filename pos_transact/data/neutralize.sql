-- disable Adyen Payement POS integration
UPDATE pos_payment_method
   SET transact_test_mode = true;
